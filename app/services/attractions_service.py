from typing import Dict, Any, List
import httpx
from fastapi import HTTPException
import logging
import os
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AttractionsService:
    def __init__(self):
        self.opentripmap_base_url = "http://api.opentripmap.com/0.1/en/places"
        self.api_key = os.getenv("OPENTRIPMAP_API_KEY")
        if not self.api_key:
            logger.error("OPENTRIPMAP_API_KEY not set")
            raise HTTPException(status_code=500, detail="OpenTripMap API key not configured")

    async def get_attractions(self, country: str) -> Dict[str, Any]:
        normalized_country = country.title()
        logger.info(f"Fetching attractions for {normalized_country}")
        async with httpx.AsyncClient() as client:
            try:
                # Throttle to 1 request/second
                time.sleep(1.0)
                # Step 1: Get country coordinates
                url = f"{self.opentripmap_base_url}/geoname?name={normalized_country}&apikey={self.api_key}"
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                if data.get("status") != "OK":
                    logger.error(f"OpenTripMap geocode error: {data}")
                    raise HTTPException(status_code=500, detail="Error geocoding country")
                lon, lat = data["lon"], data["lat"]

                # Step 2: Get attractions near coordinates
                time.sleep(1.0)
                url = f"{self.opentripmap_base_url}/radius?radius=100000&lon={lon}&lat={lat}&kinds=cultural,natural&limit=10&apikey={self.api_key}"
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                attractions: List[Dict[str, Any]] = [
                    {
                        "name": feature["properties"]["name"],
                        "kind": feature["properties"]["kinds"],
                        "coordinates": {
                            "lon": feature["geometry"]["coordinates"][0],
                            "lat": feature["geometry"]["coordinates"][1]
                        }
                    }
                    for feature in data["features"] if feature["properties"]["name"]
                ]
                logger.info(f"Returning {len(attractions)} attractions for {country}")
                return {"country": country, "attractions": attractions}
            except httpx.HTTPStatusError as e:
                logger.error(f"OpenTripMap error: {e.response.status_code} - {e.response.text}")
                raise HTTPException(status_code=e.response.status_code, detail=f"OpenTripMap error: {e.response.text}")
            except httpx.HTTPError as e:
                logger.error(f"Network error: {str(e)}")
                raise HTTPException(status_code=502, detail=f"Error connecting to OpenTripMap: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Error fetching attractions: {str(e)}")