"""
Health check endpoint.

Confirms two things: the app is running, and it can reach the database.
Useful locally and as a smoke test after deployment.
"""
from flask import Blueprint, jsonify
from sqlalchemy import text

from app.extensions import db

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health():
    """Returns the status of the app and the database connection."""
    try:
        # The simplest possible query, just to test the connection.
        # text() is required in SQLAlchemy 2.x for raw SQL.
        db.session.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {e}"

    return jsonify({
        "app": "ok",
        "database": db_status,
    })