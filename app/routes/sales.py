"""
Question 1 endpoints — geographic analysis.

Routes handle HTTP only: read parameters, call the service, return JSON.
"""
from flask import Blueprint, jsonify, request

from app.services.analytics import revenue_by_country, monthly_revenue_by_country

# url_prefix means every route here starts with /api/vendas.
sales_bp = Blueprint("sales", __name__, url_prefix="/api/vendas")


@sales_bp.route("/por-pais", methods=["GET"])
def por_pais():
    """GET /api/vendas/por-pais?top=5"""
    # 'top' has a default because the question still makes sense without it.
    top = request.args.get("top", 5, type=int)

    result = revenue_by_country(top_n=top)
    return jsonify({"data": result})


@sales_bp.route("/timeline-por-pais", methods=["GET"])
def timeline_por_pais():
    """GET /api/vendas/timeline-por-pais?pais=France"""
    # 'pais' is required: without a country there is no question to answer.
    # Better to fail with a clear message than to silently pick one.
    pais = request.args.get("pais")

    if not pais:
        return jsonify({
            "error": "Parameter 'pais' is mandatory. Example: ?pais=France"
        }), 400

    result = monthly_revenue_by_country(country=pais)
    return jsonify({"data": result})
