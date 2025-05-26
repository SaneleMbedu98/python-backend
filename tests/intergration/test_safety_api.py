import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_get_safety_no_advisories(client, mocker):
    # Arrange
    mock_response = {
        "country": "South Africa",
        "advisory": {
            "message": "No specific travel advisory found for South Africa",
            "score": None,
            "updated": "N/A"
        }
    }
    mocker.patch("app.services.safety_service.SafetyService.get_safety", AsyncMock(return_value=mock_response))
    
    # Act
    response = client.get("/countries/South%20Africa/safety")
    
    # Assert
    assert response.status_code == 200
    assert response.json() == mock_response

@pytest.mark.asyncio
async def test_get_safety_success(client, mocker):
    # Arrange
    mock_response = {
        "country": "South Africa",
        "advisory": {
            "message": "Exercise increased caution in South Africa due to crime.",
            "score": None,
            "updated": "2025-05-01T12:00:00Z"
        }
    }
    mocker.patch("app.services.safety_service.SafetyService.get_safety", AsyncMock(return_value=mock_response))
    
    # Act
    response = client.get("/countries/South%20Africa/safety")
    
    # Assert
    assert response.status_code == 200
    assert response.json() == mock_response

@pytest.mark.asyncio
async def test_get_safety_error(client, mocker):
    # Arrange
    mocker.patch("app.services.safety_service.SafetyService.get_safety", AsyncMock(side_effect=Exception("API error")))
    
    # Act
    response = client.get("/countries/South%20Africa/safety")
    
    # Assert
    assert response.status_code == 500
    assert "Error fetching safety" in response.json()["detail"]