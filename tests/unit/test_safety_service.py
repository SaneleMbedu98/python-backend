import pytest
import pytest_asyncio
from app.services.safety_service import SafetyService
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_get_safety_no_advisories(mocker, safety_service):
    # Arrange
    mock_xml = """
    <rss version="2.0">
        <channel>
            <title>travel.state.gov: Travel Advisories</title>
            <link>travel.state.gov: Travel Advisories</link>
            <description>Travel Advisories</description>
        </channel>
    </rss>
    """
    mocker.patch("httpx.AsyncClient.get", AsyncMock(return_value=type("Response", (), {"text": mock_xml, "raise_for_status": lambda: None})()))
    
    # Act
    result = await safety_service.get_safety("South Africa")
    
    # Assert
    assert result["country"] == "South Africa"
    assert result["advisory"]["message"] == "No specific travel advisory found for South Africa"
    assert result["advisory"]["score"] is None
    assert result["advisory"]["updated"] == "N/A"

@pytest.mark.asyncio
async def test_get_safety_success(mocker, safety_service):
    # Arrange
    mock_xml = """
    <rss version="2.0">
        <channel>
            <title>travel.state.gov: Travel Advisories</title>
            <item>
                <title>South Africa Travel Advisory</title>
                <description>Exercise increased caution in South Africa due to crime.</description>
                <pubDate>2025-05-01T12:00:00Z</pubDate>
            </item>
        </channel>
    </rss>
    """
    mocker.patch("httpx.AsyncClient.get", AsyncMock(return_value=type("Response", (), {"text": mock_xml, "raise_for_status": lambda: None})()))
    
    # Act
    result = await safety_service.get_safety("South Africa")
    
    # Assert
    assert result["country"] == "South Africa"
    assert result["advisory"]["message"] == "Exercise increased caution in South Africa due to crime."
    assert result["advisory"]["score"] is None
    assert result["advisory"]["updated"] == "2025-05-01T12:00:00Z"