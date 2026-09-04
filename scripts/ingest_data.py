"""
One-off ETL script: loads the Online Retail II dataset into PostgreSQL.

Pipeline: READ -> CLEAN -> TRANSFORM -> LOAD

Run from the project root:
    python scripts/ingest_data.py
"""
import sys
from pathlib import Path

# This file lives in a subfolder, so Python cannot find the 'app' package on
# its own. Adding the project root to sys.path makes the imports below work.
# Must come before those imports, since Python reads top to bottom.
sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models.transaction import Transaction  # noqa: E402

FILE = "data/online_retail.xlsx"

# Rows written per transaction. Small enough to keep memory flat, large
# enough to avoid the overhead of committing too often.
BATCH_SIZE = 5000

# Source column name -> our column name. Keeping this mapping in one place
# means a change in the source file only affects this script.
COLUMN_MAP = {
    "Invoice": "invoice_no",
    "StockCode": "stock_code",
    "Description": "description",
    "Quantity": "quantity",
    "InvoiceDate": "invoice_date",
    "Price": "unit_price",
    "Customer ID": "customer_id",   # note the space in the original name
    "Country": "country",
}


def ingest():
    app = create_app()

    # A standalone script has no request context, so the application context
    # must be opened manually for `db` to know which database to talk to.
    with app.app_context():

        # --- READ ------------------------------------------------------
        print("Reading Excel file... (this can take a few minutes)")

        df_2009 = pd.read_excel(FILE, sheet_name="Year 2009-2010")
        df_2010 = pd.read_excel(FILE, sheet_name="Year 2010-2011")

        # Stack both sheets; ignore_index renumbers the rows from 0.
        df = pd.concat([df_2009, df_2010], ignore_index=True)
        print(f"Read {len(df):,} rows\n")

        # --- CLEAN -----------------------------------------------------
        print("Cleaning...")
        initial_rows = len(df)

        # Revenue cannot be computed without these fields.
        df = df.dropna(subset=["Invoice", "StockCode", "Quantity",
                               "Price", "InvoiceDate"])

        # Zero or negative values are not real sales.
        df = df[df["Quantity"] > 0]
        df = df[df["Price"] > 0]

        # Invoices starting with "C" are cancellations (returns). The project's
        # questions concern revenue generated, so returns are out of scope.
        # ~ negates the condition: keep rows that do NOT start with C.
        df = df[~df["Invoice"].astype(str).str.startswith("C")]

        removed = initial_rows - len(df)
        print(f"Removed {removed:,} rows")
        print(f"Kept {len(df):,} of {initial_rows:,} "
              f"({len(df) / initial_rows * 100:.1f}%)\n")

        # --- TRANSFORM -------------------------------------------------
        df = df.rename(columns=COLUMN_MAP)

        df["invoice_no"] = df["invoice_no"].astype(str)
        df["stock_code"] = df["stock_code"].astype(str)
        df["invoice_date"] = pd.to_datetime(df["invoice_date"])

        # --- LOAD ------------------------------------------------------
        total = len(df)
        print(f"Loading {total:,} transactions in batches of {BATCH_SIZE:,}...")

        for start in range(0, total, BATCH_SIZE):
            batch = df.iloc[start:start + BATCH_SIZE]

            # itertuples is significantly faster than iterrows for this.
            # String slices ([:20], [:200], [:50]) enforce the column limits
            # defined in the model, so an oversized value cannot abort the run.
            records = [
                Transaction(
                    invoice_no=row.invoice_no[:20],
                    stock_code=row.stock_code[:20],
                    description=(str(row.description)[:200]
                                 if pd.notna(row.description) else None),
                    quantity=int(row.quantity),
                    # Convert from pandas Timestamp to the standard datetime
                    # that SQLAlchemy expects.
                    invoice_date=row.invoice_date.to_pydatetime(),
                    unit_price=float(row.unit_price),
                    # pandas reads this as float (13085.0) because the column
                    # has nulls, so cast to int only when a value exists.
                    customer_id=(int(row.customer_id)
                                 if pd.notna(row.customer_id) else None),
                    country=str(row.country)[:50],
                )
                for row in batch.itertuples(index=False)
            ]

            db.session.bulk_save_objects(records)
            # Committing per batch means a mid-run failure does not discard
            # the rows already persisted.
            db.session.commit()

            loaded = min(start + BATCH_SIZE, total)
            print(f"  {loaded:,} / {total:,} ({loaded / total * 100:.0f}%)")

        print(f"\nDone. {total:,} transactions loaded.")


if __name__ == "__main__":
    ingest()