from app.models.country import CountryModel
from typing import Dict, Any, Optional
import httpx
import aiohttp
from starlette.concurrency import run_in_threadpool
from fastapi import HTTPException
import json
import os 

class CountryService:
    def __init__(self, country_model: CountryModel):
        self.country_model = country_model

    def get_all_countries(self):
        return self.country_model.find_all()

    async def get_country_details(self, name: str) -> Optional[Dict[str, Any]]:
        country = await run_in_threadpool(self.country_model.find_by_name, name)
        if not country:
            return None
        async with httpx.AsyncClient() as client:
            # Fetch coordinates from Nominatim
            url = "https://nominatim.openstreetmap.org/search"
            params = {"q": country["name"], "format": "json"}
            resp = await client.get(url, params=params, headers={"User-Agent": "country-api"})
            data = resp.json()
            if data and "boundingbox" in data[0]:
                country["coordinates"] = {"boundingbox": data[0]["boundingbox"]}
            else:
                country["coordinates"] = None

            # Get Wikipedia summary
            wiki_title = country["name"].replace(" ", "_")
            wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_title}"
            wiki_resp = await client.get(wiki_url)
            wiki_data = wiki_resp.json()
            country["wikipedia_summary"] = wiki_data.get("extract", None)

        return country

    async def make_custom_request(self, api_key: str, message: str, country: str):
            # url = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
            url = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "inputs": f"You are a helpful assistant for questions about {country}. {message}",
                "parameters": {
                    "max_new_tokens": 500,
                    "return_full_text": False,
                    "temperature": 0.7
                }
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        if isinstance(result, list) and len(result) > 0 and "generated_text" in result[0]:
                            return {"choices": [{"message": {"content": result[0]["generated_text"].strip()}}]}
                        else:
                            raise HTTPException(status_code=500, detail="Unexpected response format from Hugging Face API")
                    else:
                        error_text = await response.text()
                        raise HTTPException(status_code=response.status, detail=f"Hugging Face API error: {error_text}")

        # ... (other methods like get_country_map_data, get_country_photos, etc., remain unchanged)

    def update_country(self, name: str, update_data: dict):
        update_data = {k: v for k, v in update_data.items() if v is not None}
        if not update_data:
            raise ValueError("No valid fields to update")
        return self.country_model.update_one(name, update_data)

    async def get_country_photos(self, name: str, access_key: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "https://api.unsplash.com/search/photos",
                    params={"query": name, "client_id": access_key, "per_page": 5, "orientation": "landscape"}
                )
                response.raise_for_status()
                data = response.json()
                photos = [
                    {
                        "url": photo["urls"]["regular"],
                        "thumbnail": photo["urls"]["thumb"],
                        "description": photo.get("alt_description", "No description available"),
                        "photographer": photo["user"]["name"],
                        "source_url": photo["links"]["html"],
                        "source": "Unsplash"
                    }
                    for photo in data.get("results", [])
                ]
                return {"photos": photos, "total_results": data.get("total", 0)}
            except httpx.HTTPStatusError as e:
                raise HTTPException(status_code=e.response.status_code, detail=f"Unsplash API error: {str(e)}")
            except httpx.HTTPError as e:
                raise HTTPException(status_code=502, detail=f"Error connecting to Unsplash API: {str(e)}")

    async def get_country_pixabay_photos(self, name: str, access_key: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "https://pixabay.com/api/",
                    params={
                        "key": access_key,
                        "q": name,
                        "image_type": "photo",
                        "per_page": 5,
                        "safesearch": True
                    }
                )
                response.raise_for_status()
                data = response.json()
                photos = [
                    {
                        "url": photo["webformatURL"],
                        "thumbnail": photo["previewURL"],
                        "description": photo.get("tags", "No description available"),
                        "photographer": photo["user"],
                        "source_url": photo["pageURL"],
                        "source": "Pixabay"
                    }
                    for photo in data.get("hits", [])
                ]
                return {"photos": photos, "total_results": data.get("totalHits", 0)}
            except httpx.HTTPStatusError as e:
                raise HTTPException(status_code=e.response.status_code, detail=f"Pixabay API error: {str(e)}")
            except httpx.HTTPError as e:
                raise HTTPException(status_code=502, detail=f"Error connecting to Pixabay API: {str(e)}")

    async def get_country_pexels_photos(self, name: str, access_key: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "https://api.pexels.com/v1/search",
                    params={"query": name, "per_page": 5},
                    headers={"Authorization": access_key}
                )
                response.raise_for_status()
                data = response.json()
                photos = [
                    {
                        "url": photo["src"]["medium"],
                        "thumbnail": photo["src"]["tiny"],
                        "description": photo.get("alt", "No description available"),
                        "photographer": photo["photographer"],
                        "source_url": photo["url"],
                        "source": "Pexels"
                    }
                    for photo in data.get("photos", [])
                ]
                return {"photos": photos, "total_results": data.get("total_results", 0)}
            except httpx.HTTPStatusError as e:
                raise HTTPException(status_code=e.response.status_code, detail=f"Pexels API error: {str(e)}")
            except httpx.HTTPError as e:
                raise HTTPException(status_code=502, detail=f"Error connecting to Pexels API: {str(e)}")

    async def get_country_images(self, name: str, unsplash_key: str, pixabay_key: str, pexels_key: str) -> Dict[str, Any]:
        photos = []
        urls_seen = set()

        # Unsplash
        try:
            unsplash_photos = await self.get_country_photos(name, unsplash_key)
            for photo in unsplash_photos["photos"]:
                if photo["url"] not in urls_seen:
                    photos.append(photo)
                    urls_seen.add(photo["url"])
        except Exception as e:
            print(f"Unsplash error: {str(e)}")  # Log error, continue with other APIs

        # Pixabay
        try:
            pixabay_photos = await self.get_country_pixabay_photos(name, pixabay_key)
            for photo in pixabay_photos["photos"]:
                if photo["url"] not in urls_seen:
                    photos.append(photo)
                    urls_seen.add(photo["url"])
        except Exception as e:
            print(f"Pixabay error: {str(e)}")  # Log error, continue

        # Pexels
        try:
            pexels_photos = await self.get_country_pexels_photos(name, pexels_key)
            for photo in pexels_photos["photos"]:
                if photo["url"] not in urls_seen:
                    photos.append(photo)
                    urls_seen.add(photo["url"])
        except Exception as e:
            print(f"Pexels error: {str(e)}")  # Log error, continue

        return {"photos": photos[:15], "total_results": len(photos)}
    
    async def get_country_map_data(self, name: str) -> Dict[str, Any]:
            async with httpx.AsyncClient() as client:
                try:
                    # Fetch coordinates from Nominatim
                    url = "https://nominatim.openstreetmap.org/search"
                    params = {
                        "q": name,
                        "format": "json",
                        "polygon_geojson": 1,
                        "limit": 1
                    }
                    resp = await client.get(url, params=params, headers={"User-Agent": "country-api/1.0"})
                    resp.raise_for_status()
                    data = resp.json()
                    if not data or "boundingbox" not in data[0]:
                        raise HTTPException(status_code=404, detail="Country coordinates not found")

                    coordinates = {
                        "lat": float(data[0]["lat"]),
                        "lon": float(data[0]["lon"]),
                        "boundingbox": [
                            float(data[0]["boundingbox"][0]),  # south
                            float(data[0]["boundingbox"][1]),  # north
                            float(data[0]["boundingbox"][2]),  # west
                            float(data[0]["boundingbox"][3])   # east
                        ]
                    }

                    # Fetch capital city from MongoDB
                    country = await run_in_threadpool(self.country_model.find_by_name, name)
                    capital = country.get("capital") if country else name

                    # Fetch Mapillary images
                    mapillary_key = os.getenv("MAPILLARY_CLIENT_ID")
                    mapillary_images = []
                    if mapillary_key:
                        try:
                            mapillary_url = "https://graph.mapillary.com/v3/images"
                            mapillary_params = {
                                "access_token": mapillary_key,
                                "bbox": f"{coordinates['boundingbox'][2]},{coordinates['boundingbox'][0]},{coordinates['boundingbox'][3]},{coordinates['boundingbox'][1]}",
                                "limit": 5
                            }
                            mapillary_resp = await client.get(mapillary_url, params=mapillary_params)
                            mapillary_resp.raise_for_status()
                            mapillary_data = mapillary_resp.json()
                            mapillary_images = [
                                {
                                    "id": img["id"],
                                    "lat": img["geometry"]["coordinates"][1],
                                    "lon": img["geometry"]["coordinates"][0],
                                    "thumb_url": img.get("thumb_1024_url", "")
                                }
                                for img in mapillary_data.get("data", [])
                            ]
                        except Exception as e:
                            print(f"Mapillary error: {str(e)}")

                    # Fetch POIs from Overpass API (e.g., tourist attractions)
                    overpass_url = "https://overpass-api.de/api/interpreter"
                    overpass_query = f"""
                        [out:json];
                        (
                            node["tourism"="attraction"]({coordinates['boundingbox'][0]},{coordinates['boundingbox'][2]},{coordinates['boundingbox'][1]},{coordinates['boundingbox'][3]});
                            way["tourism"="attraction"]({coordinates['boundingbox'][0]},{coordinates['boundingbox'][2]},{coordinates['boundingbox'][1]},{coordinates['boundingbox'][3]});
                        );
                        out center;
                    """
                    try:
                        overpass_resp = await client.post(overpass_url, data={"data": overpass_query})
                        overpass_resp.raise_for_status()
                        overpass_data = overpass_resp.json()
                        pois = [
                            {
                                "name": elem.get("tags", {}).get("name", "Unknown"),
                                "lat": elem.get("lat", elem.get("center", {}).get("lat")),
                                "lon": elem.get("lon", elem.get("center", {}).get("lon")),
                                "type": elem.get("tags", {}).get("tourism", "attraction")
                            }
                            for elem in overpass_data.get("elements", [])
                        ]
                    except Exception as e:
                        print(f"Overpass error: {str(e)}")
                        pois = []

                    # Use Nominatim's GeoJSON or local fallback
                    geojson_data = data[0].get("geojson")
                    if not geojson_data:
                        try:
                            with open("app/static/geojson/ne_110m_admin_0_countries/ne_110m_admin_0_countries.geojson", "r") as f:
                                geojson_data = json.load(f)
                            country_feature = None
                            for feature in geojson_data["features"]:
                                if feature["properties"]["NAME"].lower() == name.lower():
                                    country_feature = feature
                                    break
                            if not country_feature:
                                raise HTTPException(status_code=404, detail="Country GeoJSON not found")
                            geojson_data = country_feature
                        except FileNotFoundError:
                            raise HTTPException(status_code=500, detail="GeoJSON file not found")

                    return {
                        "coordinates": coordinates,
                        "capital": capital,
                        "geojson": geojson_data,
                        "mapillary_images": mapillary_images,
                        "pois": pois
                    }
                except httpx.HTTPStatusError as e:
                    raise HTTPException(status_code=e.response.status_code, detail=f"Nominatim API error: {str(e)}")
                except httpx.HTTPError as e:
                    raise HTTPException(status_code=502, detail=f"Error connecting to Nominatim API: {str(e)}")
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Error fetching map data: {str(e)}")

        # ... (other methods like get_country_details, get_country_photos, etc., remain unchanged)