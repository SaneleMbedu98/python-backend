from typing import Dict, Any, List
import httpx
from fastapi import HTTPException
import logging
import os
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SocialService:
    def __init__(self):
        self.x_api_base_url = "https://api.twitter.com/2"
        self.x_bearer_token = os.getenv("X_BEARER_TOKEN")
        if not self.x_bearer_token or self.x_bearer_token.strip() == "":
            logger.error("X_BEARER_TOKEN not set or empty in environment variables")
            raise HTTPException(status_code=500, detail="X API token not configured")
        # Request tracking
        self.request_count = 0
        self.last_reset = time.time()
        self.max_requests_per_day = 4  # ~100 requests/month / 30 days
        self.requests_per_second = 1  # Avoid bursts

    async def get_social_posts(self, country: str) -> Dict[str, Any]:
        """
        Fetch recent posts from X about the country, excluding retweets and duplicates.
        """
        # Reset request count daily
        if time.time() - self.last_reset > 24 * 60 * 60:  # 24 hours
            self.request_count = 0
            self.last_reset = time.time()
            logger.info("Reset daily request count")

        # Check rate limit
        if self.request_count >= self.max_requests_per_day:
            logger.error("Daily X API request limit reached")
            raise HTTPException(status_code=429, detail="Daily X API request limit reached. Try again tomorrow.")

        # Use title case for consistency with currency_service
        normalized_country = country.title()
        query = f"{normalized_country} (travel OR tourism OR weather) -is:retweet"
        logger.info(f"Fetching X posts for query: {query} (Request {self.request_count + 1}/{self.max_requests_per_day})")
        headers = {"Authorization": f"Bearer {self.x_bearer_token}"}
        params = {
            "query": query,
            "max_results": 10,
            "tweet.fields": "created_at,author_id"
        }
        async with httpx.AsyncClient() as client:
            try:
                # Throttle requests
                time.sleep(1.0 / self.requests_per_second)
                response = await client.get(
                    f"{self.x_api_base_url}/tweets/search/recent",
                    headers=headers,
                    params=params
                )
                response.raise_for_status()
                self.request_count += 1
                data = response.json()
                if "data" not in data:
                    logger.error(f"X API error for {country}: {data}")
                    raise HTTPException(status_code=500, detail=f"X API error: {data.get('detail', 'No data returned')}")
                
                # Deduplicate posts by text content
                seen_texts = set()
                posts: List[Dict[str, Any]] = []
                for tweet in data["data"]:
                    text = tweet["text"]
                    if text not in seen_texts:
                        seen_texts.add(text)
                        posts.append({
                            "id": tweet["id"],
                            "text": text,
                            "created_at": tweet["created_at"],
                            "author_id": tweet["author_id"]
                        })
                
                logger.info(f"Returning {len(posts)} unique posts for {country}")
                return {"country": country, "posts": posts}
            except httpx.HTTPStatusError as e:
                logger.error(f"X API error: {e.response.status_code} - {e.response.text}")
                raise HTTPException(status_code=e.response.status_code, detail=f"X API error: {e.response.text}")
            except httpx.HTTPError as e:
                logger.error(f"Network error connecting to X API: {str(e)}")
                raise HTTPException(status_code=502, detail=f"Error connecting to X API: {str(e)}")
            except ValueError as e:
                logger.error(f"Invalid header or configuration: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Invalid X API configuration: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error fetching X posts: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Error fetching X posts: {str(e)}")