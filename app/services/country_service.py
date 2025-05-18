import httpx
from app.models.country import CountryModel
from typing import Dict, Any, Optional
from starlette.concurrency import run_in_threadpool

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
            resp = await client.get(url, params=params, headers={"User-Agent": "flask-app"})
            data = resp.json()
            if data and "boundingbox" in data[0]:
                country["coordinates"] = {"boundingbox": data[0]["boundingbox"]}
            else:
                country["coordinates"] = None

            # Get World Bank economic info
            iso_codes = {"South Africa": "ZAF"}
            code = iso_codes.get(country["name"])
            if code:
                wb_url = f"http://api.worldbank.org/v2/country/{code}?format=json"
                wb_resp = await client.get(wb_url)
                wb_data = wb_resp.json()
                if (
                    isinstance(wb_data, list)
                    and len(wb_data) > 1
                    and wb_data[1]
                    and isinstance(wb_data[1][0], dict)
                ):
                    econ = wb_data[1][0]
                    country["economic_info"] = {
                        "incomeLevel": econ.get("incomeLevel"),
                        "lendingType": econ.get("lendingType"),
                    }
                else:
                    country["economic_info"] = None
            else:
                country["economic_info"] = None

            # Get Wikipedia summary
            wiki_title = country["name"].replace(" ", "_")
            wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_title}"
            wiki_resp = await client.get(wiki_url)
            wiki_data = wiki_resp.json()
            country["wikipedia_summary"] = wiki_data.get("extract", None)

        return country

    def update_country(self, name: str, update_data: dict):
        update_data = {k: v for k, v in update_data.items() if v is not None}
        if not update_data:
            raise ValueError("No valid fields to update")
        return self.country_model.update_one(name, update_data)