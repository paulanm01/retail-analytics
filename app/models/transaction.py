"""Transaction model — one sales line from the Online Retail II dataset."""
from app.extensions import db


class Transaction(db.Model):
    __tablename__ = "transactions"

    # Primary key, filled automatically by PostgreSQL (1, 2, 3, ...)
    id = db.Column(db.Integer, primary_key=True)

    # Indexes are set on the columns used for filtering and grouping in the
    # analytics queries. Each index speeds up reads but costs space and makes
    # writes slower, so they are not applied to every column.
    invoice_no = db.Column(db.String(20), index=True, nullable=False)
    stock_code = db.Column(db.String(20), index=True, nullable=False)
    description = db.Column(db.String(200), index=False, nullable=True)
    quantity = db.Column(db.Integer, index=False, nullable=False)
    invoice_date = db.Column(db.DateTime, index=True, nullable=False)
    unit_price = db.Column(db.Float, index=False, nullable=False)
    # Nullable: many sales in the dataset have no identified customer.
    customer_id = db.Column(db.Integer, index=True, nullable=True)
    country = db.Column(db.String(50), index=True, nullable=False)

    @property
    def total(self):
        """Line total. Calculated on access, not stored in the database."""
        return self.quantity * self.unit_price

    def __repr__(self):
        return f"<Transaction {self.invoice_no} - {self.stock_code}>"