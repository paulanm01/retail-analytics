"""
Inspects the source Excel file before designing the database table.

Prints the sheet names, the column names and a small sample, so the model
can be built against what the data actually looks like.

Run from the project root:
    python scripts/peek_data.py
"""
import pandas as pd

FILE = "data/online_retail.xlsx"

# ExcelFile opens the file without loading all the data into memory.
excel = pd.ExcelFile(FILE)

print("Sheets found:")
for name in excel.sheet_names:
    print(f"  - {name}")

# nrows=5 keeps this instant instead of reading a million rows.
first_sheet = excel.sheet_names[0]
df = pd.read_excel(FILE, sheet_name=first_sheet, nrows=5)

print(f"\nColumns in '{first_sheet}':")
for col in df.columns:
    print(f"  - {col}")

print("\nFirst 5 rows:")
print(df)

# Note: types inferred from 5 rows can be misleading. Invoice looks numeric
# here, but the full dataset contains values like "C489449" for returns.
print("\nInferred data types:")
print(df.dtypes)