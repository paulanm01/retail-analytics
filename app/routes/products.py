"""
Question 2 endpoints — product analysis.

Routes handle HTTP only: read parameters, call the service, return JSON.
"""
from flask import Blueprint, jsonify, request

from app.services.analytics import top_products, declining_products

products_bp = Blueprint("products", __name__, url_prefix="/api/produtos")

# The API uses Portuguese parameter values, as defined in the project spec,
# while the service layer uses English. Translating here keeps that
# difference at the edge of the API.
SORT_OPTIONS = {"receita": "revenue", "quantidade": "quantity"}


@products_bp.route("/top", methods=["GET"])
def top():
    """GET /api/produtos/top?por=receita&limite=20"""
    por = request.args.get("por", "receita")
    limite = request.args.get("limite", 20, type=int)

    # Validate before the lookup below, which would raise a KeyError
    # on an unknown value.
    if por not in SORT_OPTIONS:
        return jsonify({
            "error": "Parameter 'por' must be 'receita' or 'quantidade'."
        }), 400

    result = top_products(by=SORT_OPTIONS[por], top_n=limite)
    return jsonify({"data": result})


@products_bp.route("/tendencias-queda", methods=["GET"])
def tendencias_queda():
    """GET /api/produtos/tendencias-queda?limite=20&min_receita=100"""
    limite = request.args.get("limite", 20, type=int)
    # float, not int: this is a monetary threshold.
    min_receita = request.args.get("min_receita", 100, type=float)

    result = declining_products(top_n=limite, min_revenue=min_receita)
    return jsonify({"data": result})