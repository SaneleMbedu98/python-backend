from flask import Blueprint, jsonify, request, abort
from app.services.country_service import CountryService
from app.schemas.country_schema import CountryUpdate
import asyncio

country_bp = Blueprint("country", __name__, url_prefix="/countries")

def init_routes(country_service: CountryService):
    @country_bp.route("/", methods=["GET"])
    def get_countries():
        try:
            countries = country_service.get_all_countries()
            return jsonify({"countries": countries})
        except Exception as e:
            abort(500, description=str(e))

    @country_bp.route("/<name>", methods=["GET"])
    def get_country(name: str):
        try:
            country = asyncio.run(country_service.get_country_details(name))
            if country:
                return jsonify(country)
            abort(404, description="Country not found")
        except Exception as e:
            abort(500, description=str(e))

    @country_bp.route("/<name>", methods=["PUT", "PATCH"])
    def update_country(name: str):
        try:
            update_data = request.get_json()
            if not update_data:
                abort(400, description="No data provided")
            update = CountryUpdate(**update_data)
            updated = country_service.update_country(name, update.dict())
            if updated:
                return jsonify(updated)
            abort(404, description="Country not found")
        except ValueError as e:
            abort(400, description=str(e))
        except Exception as e:
            abort(500, description=str(e))

    @country_bp.route("/<name>", methods=["DELETE"])
    def delete_country(name: str):
        abort(405, description="Deleting countries is not allowed.")

    return country_bp