from fastapi import FastAPI, APIRouter, HTTPException, Path, Body, status, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import os
from app.models.country import CountryModel
from app.services.country_service import CountryService
import openai

app = FastAPI()
router = APIRouter()

app = FastAPI(
    title="Saneles Country API",
    description="API for country data",
    version="1.0.0"
)

class ChatRequest(BaseModel):
    message: str
    country: str

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # if for any reason you we need to be specific["http://localhost:3000"]
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

openai.api_key="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"
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

class ChatRequest(BaseModel):
    message: str
    country: str

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
        detail="Deleting countries is not sallowed."
    )

#chat bot intergration
@router.post("/api/chat", tags=["chat"])
async def chat_endpoint(chat: ChatRequest):
    try:
        # Using the custom function to make the request
        result = await country_service.make_custom_request(openai.api_key, chat.message, chat.country)
        reply = result['choices'][0]['message']['content']
        return {"reply": reply}
    except Exception as e:
        print(f"Error: {str(e)}")  # Log error for debugging
        return {"reply": f"Sorry, there was an error contacting the AI: {str(e)}"}


app.include_router(router)