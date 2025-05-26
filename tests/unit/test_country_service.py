import pytest
import pytest_asyncio
from app.services.country_service import CountryService
from app.models.country import CountryModel
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_get_country_details_success(country_service, mock_mongo):
    # Arrange
    mock_mongo.insert_one({
        "name": "South Africa",
        "population": 59308690,
        "capital": "Pretoria",
        "flag": "https://flagcdn.com/w320/za.png"
    })
    
    # Act
    result = await country_service.get_country_details("South Africa")
    
    # Assert
    assert result["name"] == "South Africa"
    assert result["population"] == 59308690
    assert result["capital"] == "Pretoria"

@pytest.mark.asyncio
async def test_get_country_details_not_found(country_service):
    # Act
    result = await country_service.get_country_details("Nonexistent")
    
    # Assert
    assert result is None

@pytest.mark.asyncio
async def test_get_country_pixabay_photos(mocker, country_service):
    # Arrange
    mock_response = {
        "hits": [
            {"webformatURL": "http://pixabay.com/photo1", "tags": "travel", "user": "user1"}
        ]
    }
    mocker.patch("httpx.AsyncClient.get", AsyncMock(return_value=type("Response", (), {"json": lambda: mock_response, "raise_for_status": lambda: None})()))
    
    # Act
    result = await country_service.get_country_pixabay_photos("South Africa", "fake-key")
    
    # Assert
    assert result["country"] == "South Africa"
    assert len(result["photos"]) == 1
    assert result["photos"][0]["url"] == "http://pixabay.com/photo1"