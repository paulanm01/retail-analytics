"""
Question 3 endpoints — customers and temporal patterns.

Routes handle HTTP only: call the service, return JSON.
"""
from flask import Blueprint, jsonify

from app.services.analytics import customer_kpis, temporal_patterns

# Only /api here, since these two routes live under different sections
# (/api/clientes and /api/vendas).
customers_bp = Blueprint("customers", __name__, url_prefix="/api")


@customers_bp.route("/clientes/kpis", methods=["GET"])
def clientes_kpis():
    """GET /api/clientes/kpis"""
    kpis = customer_kpis()
    return jsonify({"data": kpis})


@customers_bp.route("/vendas/padroes-temporais", methods=["GET"])
def padroes_temporais():
    """GET /api/vendas/padroes-temporais"""
    patterns = temporal_patterns()
    return jsonify({"data": patterns})