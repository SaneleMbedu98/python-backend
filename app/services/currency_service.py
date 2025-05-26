from typing import Dict, Any
import httpx
from fastapi import HTTPException
import logging
import os
import json
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CurrencyService:
    def __init__(self):
        self.exchange_rate_base_url = "https://v6.exchangerate-api.com/v6"
        self.api_key = os.getenv("EXCHANGERATE_API_KEY")
        if not self.api_key:
            logger.error("EXCHANGERATE_API_KEY not set in environment variables")
            raise HTTPException(status_code=500, detail="ExchangeRate-API key not configured")
        # Load country-to-currency mappings from JSON file
        self.country_currencies = self._load_currencies()

    def _load_currencies(self) -> Dict[str, str]:
        """
        Load country-to-currency mappings from app/static/currencies.json.
        Returns a dictionary or raises an exception if loading fails.
        """
        json_file_path = Path(__file__).parent.parent / "static" / "currencies.json"
        logger.info(f"Attempting to load currency mappings from {json_file_path}")

        try:
            with open(json_file_path, "r") as file:
                currencies = json.load(file)
                if not isinstance(currencies, dict):
                    logger.error(f"Invalid format in {json_file_path}: expected a dictionary")
                    raise ValueError("Currency mappings must be a JSON object")
                logger.info(f"Loaded currencies: {list(currencies.keys())}")
                return currencies
        except FileNotFoundError:
            logger.error(f"Currency file not found: {json_file_path}")
            raise HTTPException(status_code=500, detail=f"Currency file not found: {json_file_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {json_file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Invalid JSON in currency file: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error loading {json_file_path}: {str(e)} (Type: {type(e).__name__})")
            raise HTTPException(status_code=500, detail=f"Error loading currency file: {str(e)}")

    async def convert_currency(self, country: str, amount: float, from_currency: str) -> Dict[str, Any]:
        """
        Convert an amount from a given currency to the country's local currency.
        """
        # Normalize country name to title case for consistent lookup
        normalized_country = country.title()
        to_currency = self.country_currencies.get(normalized_country, "USD")  # Default to USD if not found
        logger.info(f"Converting {amount} {from_currency} to {to_currency} for {normalized_country} (original: {country})")

        # Fetch from ExchangeRate-API
        async with httpx.AsyncClient() as client:
            try:
                url = f"{self.exchange_rate_base_url}/{self.api_key}/pair/{from_currency}/{to_currency}"
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

                if data["result"] != "success":
                    logger.error(f"ExchangeRate-API error for {from_currency} to {to_currency}: {data}")
                    raise HTTPException(status_code=500, detail=f"ExchangeRate-API error: {data.get('error-type', 'Unknown error')}")

                rate = data["conversion_rate"]
                converted = amount * rate

                return {
                    "country": country,  # Return original case for consistency
                    "from": f"{amount:.2f} {from_currency}",
                    "to": f"{converted:.2f} {to_currency}",
                    "exchange_rate": rate
                }
            except httpx.HTTPStatusError as e:
                logger.error(f"ExchangeRate-API error: {e.response.status_code} - {e.response.text}")
                raise HTTPException(status_code=e.response.status_code, detail=f"ExchangeRate-API error: {e.response.text}")
            except httpx.HTTPError as e:
                logger.error(f"Network error connecting to ExchangeRate-API: {str(e)}")
                raise HTTPException(status_code=502, detail=f"Error connecting to ExchangeRate-API: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error processing currency conversion: {str(e)} (Type: {type(e).__name__})")
                raise HTTPException(status_code=500, detail=f"Error processing currency conversion: {str(e)} (Type: {type(e).__name__})")