"""
Analytics service — functions that answer the project's business questions.

These functions know nothing about HTTP: they take parameters and return data.
Keeping them independent of Flask means they can be tested directly in
`flask shell`, which isolates calculation errors from request-handling errors.
"""
from datetime import timedelta

import pandas as pd

from app.extensions import db


def revenue_by_country(top_n=5):
    """
    Question 1a: the N countries generating the most revenue.

    Returns a list of dicts:
        [{"country": "United Kingdom", "revenue": 17870977.78}, ...]
    """
    query = "SELECT country, quantity, unit_price FROM transactions"
    df = pd.read_sql(query, db.engine)

    df["revenue"] = df["quantity"] * df["unit_price"]

    revenue_by_country_series = df.groupby("country")["revenue"].sum()
    top_countries = revenue_by_country_series.sort_values(ascending=False).head(top_n)

    # Rounded only after aggregation, so floating-point errors do not
    # accumulate across the ~1M rows.
    top_countries = top_countries.round(2)

    return top_countries.reset_index().to_dict(orient="records")


def monthly_revenue_by_country(country):
    """
    Question 1b: monthly revenue evolution for a single country.

    Returns a chronologically ordered list of dicts:
        [{"month": "2009-12", "revenue": 12345.67}, ...]
    """
    # Filtering in SQL rather than in pandas: for one country this returns a
    # few thousand rows instead of ~1M, and the country column is indexed.
    # The %(country)s placeholder passes the value as data, never as SQL,
    # which prevents SQL injection.
    query = """
        SELECT invoice_date, quantity, unit_price
        FROM transactions
        WHERE country = %(country)s
    """
    df = pd.read_sql(query, db.engine, params={"country": country})

    # Guard clause: with no rows, pandas cannot infer that invoice_date is a
    # datetime column, and the .dt accessor below would raise.
    if df.empty:
        return []

    df["revenue"] = df["quantity"] * df["unit_price"]

    # "2010-03-15 14:32" becomes "2010-03". Cast to str because pandas'
    # Period type is not JSON serialisable. The YYYY-MM format also sorts
    # alphabetically in chronological order.
    df["month"] = df["invoice_date"].dt.to_period("M").astype(str)

    monthly_revenue = df.groupby("month")["revenue"].sum()

    # sort_index() because the month became the index during groupby.
    monthly_revenue = monthly_revenue.sort_index()

    return monthly_revenue.round(2).reset_index().to_dict(orient="records")


def top_products(by="revenue", top_n=20):
    """
    Question 2a: the N best-selling products.

    by: "revenue" to rank by revenue, "quantity" to rank by units sold.

    Returns:
        [{"stock_code": "85123A", "description": "...",
          "quantity": 2313, "revenue": 5678.90}, ...]
    """
    # Fail fast: an unexpected value here would otherwise produce a silently
    # wrong ranking further down.
    if by not in ("revenue", "quantity"):
        raise ValueError("by must be 'revenue' or 'quantity'")

    query = """
        SELECT stock_code, description, quantity, unit_price
        FROM transactions
    """
    df = pd.read_sql(query, db.engine)

    df["revenue"] = df["quantity"] * df["unit_price"]

    # "first" on description because text cannot be summed — we just need a
    # readable label for each product code.
    products = df.groupby("stock_code").agg({
        "quantity": "sum",
        "revenue": "sum",
        "description": "first",
    })

    top = products.sort_values(by, ascending=False).head(top_n)

    # Only the monetary column is rounded; rounding the whole DataFrame would
    # turn the integer quantities into floats.
    top["revenue"] = top["revenue"].round(2)

    return top.reset_index().to_dict(orient="records")


def declining_products(top_n=20, min_revenue=100):
    """
    Question 2b: products with the steepest revenue decline, comparing the
    last 3 months against the 3 months before that.

    min_revenue: minimum revenue in the earlier period for a product to be
                 considered, filtering out statistically meaningless drops.

    Returns, from the steepest decline downwards:
        [{"stock_code": "...", "description": "...",
          "revenue_previous": 500.0, "revenue_recent": 200.0,
          "change_pct": -60.0}, ...]
    """
    query = """
        SELECT stock_code, description, quantity, unit_price, invoice_date
        FROM transactions
    """
    df = pd.read_sql(query, db.engine)
    df["revenue"] = df["quantity"] * df["unit_price"]

    # Windows are anchored to the dataset's most recent date, not to today.
    # The data ends in 2011, so datetime.now() would produce empty periods.
    max_date = df["invoice_date"].max()
    recent_start = max_date - timedelta(days=90)
    previous_start = max_date - timedelta(days=180)

    recent = df[df["invoice_date"] > recent_start]
    previous = df[(df["invoice_date"] > previous_start) &
                  (df["invoice_date"] <= recent_start)]

    # reset_index() turns stock_code back into a regular column, which the
    # merge below needs as its join key.
    recent_agg = recent.groupby("stock_code").agg({
        "revenue": "sum",
        "description": "first",
    }).reset_index()

    previous_agg = previous.groupby("stock_code").agg({
        "revenue": "sum",
    }).reset_index()

    # Equivalent to a SQL INNER JOIN. Both frames have a "revenue" column,
    # so the suffixes produce revenue_recent and revenue_previous.
    # inner: a product missing from either period has nothing to compare.
    comparison = recent_agg.merge(
        previous_agg,
        on="stock_code",
        suffixes=("_recent", "_previous"),
        how="inner",
    )

    # Without this threshold, a product falling from EUR 5 to EUR 2 would top
    # the list at -60% while being irrelevant to the business.
    # .copy() avoids pandas' SettingWithCopyWarning when writing below.
    comparison = comparison[comparison["revenue_previous"] >= min_revenue].copy()

    if comparison.empty:
        return []

    comparison["change_pct"] = (
        (comparison["revenue_recent"] - comparison["revenue_previous"])
        / comparison["revenue_previous"]
    ) * 100

    # ascending=True because declines are negative: -80 comes before -10.
    declining = comparison[comparison["change_pct"] < 0].sort_values(
        "change_pct",
        ascending=True,
    ).head(top_n).copy()

    declining["revenue_recent"] = declining["revenue_recent"].round(2)
    declining["revenue_previous"] = declining["revenue_previous"].round(2)
    declining["change_pct"] = declining["change_pct"].round(1)

    # Explicit column selection controls the key order in the JSON response.
    return declining[[
        "stock_code", "description",
        "revenue_previous", "revenue_recent", "change_pct",
    ]].to_dict(orient="records")


def customer_kpis():
    """
    Question 3a: key indicators about customers and transactions.

    Returns a single dict rather than a list:
        {"total_revenue": ..., "total_transactions": ...,
         "avg_ticket": ..., "unique_customers": ...,
         "recurring_customers": ..., "recurring_pct": ...,
         "avg_revenue_per_customer": ...}
    """
    query = """
        SELECT invoice_no, customer_id, quantity, unit_price
        FROM transactions
    """
    df = pd.read_sql(query, db.engine)
    df["revenue"] = df["quantity"] * df["unit_price"]

    total_revenue = df["revenue"].sum()

    # A transaction is one invoice, not one table row: a single invoice spans
    # several rows, one per product. Counting rows would give the average
    # value of a line item, which means nothing to the business.
    total_transactions = df["invoice_no"].nunique()
    avg_ticket = total_revenue / total_transactions

    # Many sales have no customer identifier. Per-customer metrics must
    # exclude them, otherwise the figures are inflated.
    identified = df.dropna(subset=["customer_id"])
    unique_customers = identified["customer_id"].nunique()

    # A recurring customer has more than one invoice. The comparison yields a
    # boolean Series, and summing it counts the True values.
    invoices_per_customer = identified.groupby("customer_id")["invoice_no"].nunique()
    recurring_customers = (invoices_per_customer > 1).sum()

    avg_revenue_per_customer = identified["revenue"].sum() / unique_customers

    # Cast to native Python types: pandas returns numpy types, which
    # Flask's jsonify cannot serialise.
    return {
        "total_revenue": float(round(total_revenue, 2)),
        "total_transactions": int(total_transactions),
        "avg_ticket": float(round(avg_ticket, 2)),
        "unique_customers": int(unique_customers),
        "recurring_customers": int(recurring_customers),
        "recurring_pct": float(round(recurring_customers / unique_customers * 100, 1)),
        "avg_revenue_per_customer": float(round(avg_revenue_per_customer, 2)),
    }


def temporal_patterns():
    """
    Question 3b: purchasing patterns by weekday and by month of the year.

    Returns a dict with two lists:
        {"by_weekday": [{"weekday": "Monday", "revenue": ..., "transactions": ...}, ...],
         "by_month":   [{"month": 1, "revenue": ..., "transactions": ...}, ...]}
    """
    query = """
        SELECT invoice_no, invoice_date, quantity, unit_price
        FROM transactions
    """
    df = pd.read_sql(query, db.engine)
    df["revenue"] = df["quantity"] * df["unit_price"]

    # Two weekday columns: the number sorts correctly (Monday to Sunday),
    # the name is what the API consumer actually wants to read.
    df["weekday_num"] = df["invoice_date"].dt.dayofweek
    df["weekday"] = df["invoice_date"].dt.day_name()
    df["month"] = df["invoice_date"].dt.month

    # Grouping by both columns keeps the numeric ordering while carrying the
    # readable name through. nunique() counts distinct invoices per group.
    by_weekday = df.groupby(["weekday_num", "weekday"]).agg({
        "revenue": "sum",
        "invoice_no": "nunique",
    }).reset_index().sort_values("weekday_num")

    by_month = df.groupby("month").agg({
        "revenue": "sum",
        "invoice_no": "nunique",
    }).reset_index().sort_values("month")

    # After nunique() the column is still named invoice_no but holds a count.
    by_weekday = by_weekday.rename(columns={"invoice_no": "transactions"})
    by_weekday["revenue"] = by_weekday["revenue"].round(2)
    # weekday_num existed only to sort; it is not part of the API contract.
    by_weekday = by_weekday.drop(columns=["weekday_num"])

    by_month = by_month.rename(columns={"invoice_no": "transactions"})
    by_month["revenue"] = by_month["revenue"].round(2)

    return {
        "by_weekday": by_weekday.to_dict(orient="records"),
        "by_month": by_month.to_dict(orient="records"),
    }