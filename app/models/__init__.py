"""
Model imports.

Flask-Migrate only knows about models that have been imported somewhere.
Without this file, migrations would be generated empty.
"""
from app.models.transaction import Transaction

__all__ = ["Transaction"]
