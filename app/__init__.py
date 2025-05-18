from flask import Flask, Blueprint, jsonify, request, abort
from app.services.country_service import CountryService
from app.models.country import CountryModel
import os

country_bp = Blueprint("country", __name__, url_prefix="/countries")

def create_app():
    app = Flask(__name__)
    # Use environment variables or config for these values
    mongodb_url = os.environ.get("MONGODB_URL", "mongodb://host.docker.internal:27017")
    db_name = os.environ.get("MONGODB_DB", "testdb")
    collection_name = os.environ.get("MONGODB_COLLECTION", "countries")
    country_model = CountryModel(mongodb_url, db_name, collection_name)
    country_service = CountryService(country_model)
    bp = init_routes(country_service)
    app.register_blueprint(bp)
    return app

def init_routes(country_service):
    @country_bp.route("/", methods=["GET"])
    def get_countries():
        countries = country_service.get_all_countries()
        return jsonify({"countries": countries})

    @country_bp.route("/<name>", methods=["GET"])
    def get_country(name):
        country = country_service.get_country_by_name(name)
        if country:
            return jsonify(country)
        abort(404, description="Country not found")

    return country_bp