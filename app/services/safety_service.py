from typing import Dict, Any
import httpx
from fastapi import HTTPException
import logging
import xmltodict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SafetyService:
    def __init__(self):
        self.travel_advisory_url = "https://travel.state.gov/_res/rss/TAs.xml"

    async def get_safety(self, country: str) -> Dict[str, Any]:
        normalized_country = country.title()
        logger.info(f"Fetching safety advisories for {normalized_country}")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.travel_advisory_url)
                response.raise_for_status()
                data = xmltodict.parse(response.text)
                advisories = data["rss"]["channel"]["item"]
                for advisory in advisories:
                    if advisory["title"].lower().startswith(normalized_country.lower()):
                        result = {
                            "country": country,
                            "advisory": {
                                "message": advisory["description"],
                                "score": None,  # State Dept uses levels (1-4), not scores
                                "updated": advisory["pubDate"]
                            }
                        }
                        logger.info(f"Returning safety advisory for {country}")
                        return result
                logger.error(f"Country not found: {normalized_country}")
                raise HTTPException(status_code=404, detail=f"Safety data not found for {normalized_country}")
            except httpx.HTTPStatusError as e:
                logger.error(f"Travel-Advisory error: {e.response.status_code} - {e.response.text}")
                raise HTTPException(status_code=e.response.status_code, detail=f"Travel-Advisory error: {e.response.text}")
            except httpx.HTTPError as e:
                logger.error(f"Network error: {str(e)}")
                raise HTTPException(status_code=502, detail=f"Error connecting to Travel-Advisory: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Error fetching safety advisories: {str(e)}")