
from typing import Dict, Any, Optional
import httpx
from fastapi import HTTPException
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WeatherService:
    def __init__(self):
        self.weather_base_url = "https://api.open-meteo.com/v1/forecast"
        self.geocode_base_url = "https://nominatim.openstreetmap.org/search"

    async def get_weather(self, country: str) -> Dict[str, Any]:
        """
        Fetch weather data for a country by first retrieving its coordinates from Nominatim.
        """
        # Step 1: Fetch coordinates from Nominatim
        logger.info(f"Fetching coordinates for {country}")
        coordinates = await self._get_coordinates(country)
        if not coordinates:
            logger.error(f"No coordinates found for {country}")
            raise HTTPException(status_code=404, detail=f"No coordinates found for {country}")

        lat, lon = coordinates["lat"], coordinates["lon"]
        logger.info(f"Using coordinates for {country}: lat={lat}, lon={lon}")

        # Step 2: Fetch weather from Open-Meteo
        logger.info(f"Fetching weather from Open-Meteo for {country} at lat={lat}, lon={lon}")
        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": True,
            "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_probability_max", "weathercode"],
            "timezone": "auto"
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.weather_base_url, params=params)
                response.raise_for_status()
                data = response.json()

                if "current_weather" not in data or "daily" not in data:
                    logger.error(f"Invalid Open-Meteo response for {country}: {data}")
                    raise HTTPException(status_code=500, detail="Invalid Open-Meteo response format")

                result = {
                    "country": country,
                    "coordinates": {"lat": lat, "lon": lon},
                    "current": {
                        "temperature": data["current_weather"].get("temperature", "N/A"),
                        "weather": self._weather_code_to_text(data["current_weather"].get("weathercode", 0)),
                        "wind_speed": data["current_weather"].get("windspeed", "N/A")
                    },
                    "daily": [
                        {
                            "date": data["daily"]["time"][i],
                            "max_temp": data["daily"]["temperature_2m_max"][i],
                            "min_temp": data["daily"]["temperature_2m_min"][i],
                            "precipitation_prob": data["daily"]["precipitation_probability_max"][i],
                            "weather": self._weather_code_to_text(data["daily"]["weathercode"][i])
                        }
                        for i in range(min(7, len(data["daily"]["time"])))
                    ]
                }
                return result
            except httpx.HTTPStatusError as e:
                logger.error(f"Open-Meteo API error for {country}: {e.response.status_code} - {e.response.text}")
                raise HTTPException(status_code=e.response.status_code, detail=f"Open-Meteo API error: {e.response.text}")
            except httpx.HTTPError as e:
                logger.error(f"Network error connecting to Open-Meteo for {country}: {str(e)}")
                raise HTTPException(status_code=502, detail=f"Error connecting to Open-Meteo API: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error processing weather for {country}: {str(e)} (Type: {type(e).__name__})")
                raise HTTPException(status_code=500, detail=f"Error processing weather data: {str(e)} (Type: {type(e).__name__})")

    async def _get_coordinates(self, country: str) -> Optional[Dict[str, float]]:
        """
        Fetch coordinates for a country using Nominatim API.
        Returns a dictionary with 'lat' and 'lon' or None if not found.
        """
        async with httpx.AsyncClient() as client:
            try:
                params = {"q": country, "format": "json"}
                headers = {"User-Agent": "saneles-country-api/1.0"}
                response = await client.get(self.geocode_base_url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()

                if not data or "boundingbox" not in data[0]:
                    logger.warning(f"No valid geocoding data for {country}: {data}")
                    return None

                # Calculate centroid from boundingbox [south, north, west, east]
                boundingbox = data[0]["boundingbox"]
                try:
                    south, north, west, east = map(float, boundingbox)
                    lat = (south + north) / 2
                    lon = (west + east) / 2
                    return {"lat": lat, "lon": lon}
                except (ValueError, TypeError) as e:
                    logger.error(f"Invalid boundingbox format for {country}: {boundingbox}, error: {str(e)}")
                    return None

            except httpx.HTTPStatusError as e:
                logger.error(f"Nominatim API error for {country}: {e.response.status_code} - {e.response.text}")
                raise HTTPException(status_code=e.response.status_code, detail=f"Nominatim API error: {e.response.text}")
            except httpx.HTTPError as e:
                logger.error(f"Network error connecting to Nominatim for {country}: {str(e)}")
                raise HTTPException(status_code=502, detail=f"Error connecting to Nominatim API: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error fetching coordinates for {country}: {str(e)}")
                return None

    def _weather_code_to_text(self, code: int) -> str:
        weather_codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Light rain",
            63: "Moderate rain",
            65: "Heavy rain",
            80: "Showers",
            81: "Moderate showers",
            82: "Violent showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail"
        }
        return weather_codes.get(code, f"Unknown code {code}")