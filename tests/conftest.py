import pytest
import mongomock
from fastapi.testclient import TestClient
from app.main import app, country_model, CountryModel
from app.services.country_service import CountryService
from app.services.safety_service import SafetyService
import os

@pytest.fixture
def client():
    """Fixture for FastAPI TestClient."""
    return TestClient(app)

@pytest.fixture
def mock_mongo():
    """Fixture for mocked MongoDB client."""
    client = mongomock.MongoClient()
    db = client["countries_db"]
    collection = db["countries"]
    yield collection
    client.drop_database("countries_db")

@pytest.fixture
def mock_country_model(mock_mongo):
    """Fixture for mocked CountryModel."""
    return CountryModel(
        mongodb_url="mongodb://localhost:27017",
        db_name="countries_db",
        collection_name="countries"
    )

@pytest.fixture
def country_service(mock_country_model):
    """Fixture for CountryService with mocked MongoDB."""
    return CountryService(mock_country_model)

@pytest.fixture
def safety_service(mocker):
    """Fixture for SafetyService with mocked HTTP requests."""
    return SafetyService()

@pytest.fixture
def mock_env(mocker):
    """Fixture to mock environment variables."""
    mocker.patch.dict(os.environ, {
        "MONGODB_URL": "mongodb://localhost:27017",
        "MONGODB_DB": "countries_db",
        "MONGODB_COLLECTION": "countries",
        "PIXABAY_API_KEY": "fake-pixabay-key",
        "MAPTILER_API_KEY": "fake-maptiler-key",
        "MAPILLARY_CLIENT_ID": "fake-mapillary-id"
    })