import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

def test_get_all_countries(client, mock_mongo):
    # Arrange
    mock_mongo.insert_many([
        {"name": "South Africa", "population": 59308690, "capital": "Pretoria"},
        {"name": "Nigeria", "population": 206139589, "capital": "Abuja"}
    ])
    
    # Act
    response = client.get("/countries/")
    
    # Assert
    assert response.status_code == 200
    assert len(response.json()["countries"]) == 2
    assert response.json()["countries"][0]["name"] == "South Africa"

def test_search_countries(client, mock_mongo):
    # Arrange
    mock_mongo.insert_one({"name": "South Africa", "population": 59308689, "capital": "Pretoria"})
    
    # Act
    response = client.get("/countries/search?q=South")
    
    # Assert
    assert response.status_code == 200
    assert len(response.json()["countries"]) == 1
    assert response.json()["countries"][0]["name"] == "South Africa"

def test_search_countries_empty_query(client):
    # Act
    response = client.get("/countries/search?q=")
    
    # Assert
    assert response.status_code == 400
    assert "query" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_get_country_by_name_not_found(client, mocker):
    # Arrange
    mocker.patch("app.services.country_service.CountryService.get_country_details", AsyncMock(return_value=None))
    
    # Act
    response = client.get("/countries/Nonexistent")
    
    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Country not found"