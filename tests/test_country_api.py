import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Welcome" in resp.json()["message"]

def test_get_all_countries(monkeypatch):
    monkeypatch.setattr("app.models.country.CountryModel.find_all", lambda self: [{"name": "South Africa"}])
    resp = client.get("/countries/")
    assert resp.status_code == 200
    assert "countries" in resp.json()
    assert resp.json()["countries"][0]["name"] == "South Africa"

def test_get_country_by_name_found(monkeypatch):
    async def fake_get_country_details(self, name):
        return {"name": name, "population": 100}
    monkeypatch.setattr("app.services.country_service.CountryService.get_country_details", fake_get_country_details)
    resp = client.get("/countries/South Africa")
    assert resp.status_code == 200
    assert resp.json()["name"] == "South Africa"

def test_get_country_by_name_not_found(monkeypatch):
    async def fake_get_country_details(self, name):
        return None
    monkeypatch.setattr("app.services.country_service.CountryService.get_country_details", fake_get_country_details)
    resp = client.get("/countries/Neverland")
    assert resp.status_code == 404

def test_update_country_success(monkeypatch):
    monkeypatch.setattr("app.models.country.CountryModel.update_one", lambda self, name, data: {"name": name, **data})
    resp = client.put("/countries/South Africa", json={"population": 60000000})
    assert resp.status_code == 200
    assert resp.json()["population"] == 60000000

def test_update_country_not_found(monkeypatch):
    monkeypatch.setattr("app.models.country.CountryModel.update_one", lambda self, name, data: None)
    resp = client.put("/countries/Neverland", json={"population": 1})
    assert resp.status_code == 404

def test_delete_country():
    resp = client.delete("/countries/South Africa")
    assert resp.status_code == 405