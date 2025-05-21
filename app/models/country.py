from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from typing import List, Dict, Any, Optional
import re

class CountryModel:
    def __init__(self, mongodb_url, db_name, collection_name):
        self.client = MongoClient(mongodb_url, serverSelectionTimeoutMS=5000)
        self.collection = self.client[db_name][collection_name]

    def normalize_name(self, name: str) -> str:
        return re.sub(r'\s+', ' ', name.strip().lower())

    def find_all(self) -> List[Dict[str, Any]]:
        try:
            return list(self.collection.find({}, {"_id": 0}))
        except ServerSelectionTimeoutError:
            raise Exception("Could not connect to MongoDB")

    def search_by_name(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            norm_query = self.normalize_name(query)
            if not norm_query:
                print("Empty query, returning empty list")
                return []
            print(f"Searching for: {norm_query}")
            countries = self.collection.find(
                {"name": {"$regex": f"^{re.escape(norm_query)}", "$options": "i"}},
                {"_id": 0}
            ).limit(limit)
            result = list(countries)
            print(f"Found {len(result)} countries")
            return result
        except ServerSelectionTimeoutError:
            raise Exception("Could not connect to MongoDB")
        except Exception as e:
            raise Exception(f"Error searching countries: {str(e)}")

    def find_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        try:
            norm_name = self.normalize_name(name)
            country = self.collection.find_one(
                {"name": {"$regex": f"^{re.escape(norm_name)}$", "$options": "i"}},
                {"_id": 0}
            )
            return country
        except ServerSelectionTimeoutError:
            raise Exception("Could not connect to MongoDB")

    def update_one(self, name: str, update_data: dict) -> Optional[Dict[str, Any]]:
        try:
            norm_name = self.normalize_name(name)
            country = self.collection.find_one(
                {"name": {"$regex": f"^{re.escape(norm_name)}$", "$options": "i"}}
            )
            if not country:
                return None
            if "name" in update_data:
                existing = self.collection.find_one(
                    {"name": {"$regex": f"^{re.escape(update_data['name'])}$", "$options": "i"}}
                )
                if existing and self.normalize_name(existing["name"]) != norm_name:
                    raise Exception("Country name already exists")
            self.collection.update_one({"_id": country["_id"]}, {"$set": update_data})
            return self.collection.find_one({"_id": country["_id"]}, {"_id": 0})
        except ServerSelectionTimeoutError:
            raise Exception("Could not connect to MongoDB")