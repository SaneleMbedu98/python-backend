from fastapi import FastAPI, APIRouter, HTTPException, Path, Body, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv
from app.models.country import CountryModel
from app.services.country_service import CountryService
from app.services.weather_service import WeatherService
from app.services.currency_service import CurrencyService
from app.services.social_service import SocialService
from app.services.attractions_service import AttractionsService
from app.services.safety_service import SafetyService
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Saneles Country API",
    description="API for country data",
    version="1.0.0"
)

router = APIRouter()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB config
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGODB_DB", "countries_db")
COLLECTION_NAME = os.getenv("MONGODB_COLLECTION", "countries")

country_model = CountryModel(MONGODB_URL, DB_NAME, COLLECTION_NAME)
country_service = CountryService(country_model)
weather_service = WeatherService()
currency_service = CurrencyService()
social_service = SocialService()
attractions_service = AttractionsService()
safety_service = SafetyService()

# Pydantic model for country update
class CountryUpdate(BaseModel):
    name: Optional[str] = Field(None, example="South Africa")
    population: Optional[int] = Field(None, example=59308690)
    capital: Optional[str] = Field(None, example="Pretoria")
    flag: Optional[str] = Field(None, example="https://flagcdn.com/w320/za.png")
    region: Optional[str] = Field(None, example="Africa")
    subregion: Optional[str] = Field(None, example="Southern Africa")
    languages: Optional[str] = Field(
        None,
        example="Afrikaans, English, Southern Ndebele, Northern Sotho, Southern Sotho, Swazi, Tswana, Tsonga, Venda, Xhosa, Zulu"
    )

# Pydantic model for chat request
class CountryChatRequest(BaseModel):
    message: str = Field(..., example="What is the culture like in South Africa?")

@app.get("/", tags=["root"])
def root():
    routes = [{"path": route.path, "methods": list(route.methods), "name": route.name}
              for route in app.routes if hasattr(route, "methods")]
    return {
        "message": "Welcome to the Saneles Country API!",
        "routes": routes
    }

@app.get("/countries/", response_model=Dict[str, List[Dict[str, Any]]], tags=["countries"])
def get_all_countries():
    try:
        countries = country_model.find_all()
        return {"countries": countries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/countries/search", response_model=Dict[str, List[Dict[str, Any]]], tags=["countries"])
async def search_countries(q: str = Query(..., description="Search query for country name", min_length=1)):
    try:
        countries = country_model.search_by_name(q)
        return {"countries": countries}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.get("/countries/{name}", response_model=Optional[Dict[str, Any]], tags=["countries"])
async def get_country_by_name(name: str = Path(..., description="Country name")):
    try:
        country = await country_service.get_country_details(name)
        if not country:
            raise HTTPException(status_code=404, detail="Country not found")
        return country
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/countries/{name}/photos", response_model=Dict[str, Any], tags=["photos"])
async def get_country_photos(name: str = Path(..., description="Country name")):
    try:
        api_key = os.getenv("UNSPLASH_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Unsplash API key not configured")
        photos = await country_service.get_country_photos(name, api_key)
        return photos
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching Unsplash photos: {str(e)}")

@app.get("/countries/{name}/pixabay_photos", response_model=Dict[str, Any], tags=["photos"])
async def get_country_pixabay_photos(name: str = Path(..., description="Country name")):
    try:
        api_key = os.getenv("PIXABAY_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Pixabay API key not configured")
        photos = await country_service.get_country_pixabay_photos(name, api_key)
        return photos
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching Pixabay photos: {str(e)}")

@app.get("/countries/{name}/pexels_photos", response_model=Dict[str, Any], tags=["photos"])
async def get_country_pexels_photos(name: str = Path(..., description="Country name")):
    try:
        api_key = os.getenv("PEXELS_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Pexels API key not configured")
        photos = await country_service.get_country_pexels_photos(name, api_key)
        return photos
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching Pexels photos: {str(e)}")

@app.get("/countries/{name}/images", response_model=Dict[str, Any], tags=["images"])
async def get_country_images(name: str = Path(..., description="Country name")):
    try:
        unsplash_key = os.getenv("UNSPLASH_API_KEY")
        pixabay_key = os.getenv("PIXABAY_API_KEY")
        pexels_key = os.getenv("PEXELS_API_KEY")
        if not all([unsplash_key, pixabay_key, pexels_key]):
            raise HTTPException(status_code=500, detail="One or more API keys not configured")
        images = await country_service.get_country_images(name, unsplash_key, pixabay_key, pexels_key)
        return images
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching images: {str(e)}")

@app.put("/countries/{name}", response_model=Dict[str, Any], tags=["countries"])
def update_country(
    name: str = Path(..., description="Country name to update"),
    update: CountryUpdate = Body(...),
):
    try:
        updated = country_model.update_one(name, update.model_dump(exclude_none=True))
        if not updated:
            raise HTTPException(status_code=404, detail="Country not found")
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.patch("/countries/{name}", response_model=Dict[str, Any], tags=["countries"])
def patch_country(
    name: str = Path(..., description="Country name to patch"),
    update: CountryUpdate = Body(...),
):
    try:
        updated = country_model.update_one(name, update.dict(exclude_none=True))
        if not updated:
            raise HTTPException(status_code=404, detail="Country not found")
        return updated
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/countries/{name}", tags=["countries"])
def delete_country(name: str):
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail="Deleting countries is not allowed."
    )

# Weather endpoint
@app.get("/countries/{name}/weather", response_model=Dict[str, Any], tags=["weather"])
async def get_country_weather(name: str = Path(..., description="Country name")):
    try:
        # Fetch weather directly using country name
        weather = await weather_service.get_weather(country=name)
        return weather
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching weather for {name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching weather: {str(e)}")

# AI chat endpoint (case-insensitive)
@app.post("/countries/{name}/chat", response_model=Dict[str, str], tags=["chat"])
async def country_chat(
    name: str = Path(..., description="Country name"),
    chat_request: CountryChatRequest = Body(...)
):
    try:
        huggingface_api_key = os.getenv("HUGGINGFACE_API_KEY")
        if not huggingface_api_key:
            raise HTTPException(status_code=500, detail="Hugging Face API key not configured")

        # Call Hugging Face API via CountryService
        result = await country_service.make_custom_request(
            api_key=huggingface_api_key,
            message=chat_request.message,
            country=name
        )
        reply = result['choices'][0]['message']['content']
        return {"reply": reply}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")
    

@app.get("/countries/{name}/currency/convert", response_model=Dict[str, Any], tags=["currency"])
async def convert_currency(
    name: str = Path(..., description="Country name"),
    amount: float = Query(..., description="Amount to convert", gt=0),
    from_currency: str = Query(..., description="Source currency code (e.g., USD)")
):
    try:
        result = await currency_service.convert_currency(country=name, amount=amount, from_currency=from_currency)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error converting currency for {name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error converting currency: {str(e)}")

@app.get("/countries/{name}/social", response_model=Dict[str, Any], tags=["social"])
async def get_social_posts(name: str = Path(..., description="Country name")):
    try:
        result = await social_service.get_social_posts(country=name)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching social posts for {name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching social posts: {str(e)}")
    
@app.get("/countries/{name}/attractions", response_model=Dict[str, Any], tags=["attractions"])
async def get_attractions(name: str = Path(..., description="Country name")):
    try:
        attractions = await attractions_service.get_attractions(country=name)
        return attractions
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching attractions for {name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching attractions: {str(e)}")
    
@app.get("/countries/{name}/safety", response_model=Dict[str, Any], tags=["safety"])
async def get_safety(name: str = Path(..., description="Country name")):
    try:
        safety = await safety_service.get_safety(country=name)
        return safety
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching safety for {name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching safety: {str(e)}")

@app.get("/countries/{name}/map", response_class=HTMLResponse, tags=["map"])
async def get_country_map(name: str = Path(..., description="Country name")):
    try:
        map_data = await country_service.get_country_map_data(name)
        maptiler_key = os.getenv("MAPTILER_API_KEY") or ""
        mapillary_key = os.getenv("MAPILLARY_CLIENT_ID") or ""

        # Serialize JSON data with proper escaping
        geojson_str = json.dumps(map_data['geojson'], ensure_ascii=False)
        mapillary_images_str = json.dumps(map_data['mapillary_images'], ensure_ascii=False)
        pois_str = json.dumps(map_data['pois'], ensure_ascii=False)

        # Generate HTML with Leaflet, Mapillary, and additional layers
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{name} Map</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        #map {{ height: 600px; width: 100%; }}
        #mapillary {{ height: 300px; width: 100%; }}
        html, body {{ height: 100%; margin: 0; padding: 0; }}
    </style>
</head>
<body>
    <div id="map"></div>
    <div id="mapillary"></div>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://unpkg.com/@mapillary/viewer@4.1.0/dist/mapillary.js"></script>
    <script>
        var map = L.map('map').setView([{map_data['coordinates']['lat']}, {map_data['coordinates']['lon']}], 5);

        // Add OpenStreetMap tiles
        var osmLayer = L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 18
        }}).addTo(map);

        // Add MapTiler satellite layer
        var satelliteLayer = L.tileLayer('https://api.maptiler.com/maps/satellite/{{z}}/{{x}}/{{y}}.jpg?key={maptiler_key}', {{
            attribution: '© <a href="https://www.maptiler.com/copyright/">MapTiler</a> © OpenStreetMap contributors',
            maxZoom: 18
        }});

        // Layer control
        var baseLayers = {{
            "OpenStreetMap": osmLayer,
            "Satellite": satelliteLayer
        }};
        L.control.layers(baseLayers).addTo(map);

        // Add GeoJSON boundary
        var geojson = {geojson_str};
        L.geoJSON(geojson, {{
            style: {{
                color: 'blue',
                weight: 2,
                fillColor: 'blue',
                fillOpacity: 0.2
            }}
        }}).addTo(map);

        // Fit map to country bounds
        var bounds = [[{map_data['coordinates']['boundingbox'][0]}, {map_data['coordinates']['boundingbox'][2]}], 
                      [{map_data['coordinates']['boundingbox'][1]}, {map_data['coordinates']['boundingbox'][3]}]];
        map.fitBounds(bounds);

        // Add Mapillary viewer
        var mapillaryImages = {mapillary_images_str};
        if (mapillaryImages.length > 0) {{
            var viewer = new Mapillary.Viewer({{
                container: 'mapillary',
                imageId: mapillaryImages[0].id,
                accessToken: '{mapillary_key}',
                component: {{ cover: false }}
            }});
            mapillaryImages.forEach(function(img) {{
                L.marker([img.lat, img.lon]).addTo(map)
                    .bindPopup('<img src="' + img.thumb_url + '" width="100" /><br>Click to view')
                    .on('click', function() {{
                        viewer.moveTo(img.id);
                    }});
            }});
        }}

        // Add POI markers
        var pois = {pois_str};
        pois.forEach(function(poi) {{
            L.marker([poi.lat, poi.lon]).addTo(map)
                .bindPopup('<b>' + poi.name + '</b><br>Type: ' + poi.type);
        }});
    </script>
</body>
</html>
"""
        return HTMLResponse(content=html_content)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating map: {str(e)}")

app.include_router(router)