from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import re

class CountryModel:
    def __init__(self, mongodb_url, db_name, collection_name):
        self.client = MongoClient(mongodb_url, serverSelectionTimeoutMS=5000)
        self.collection = self.client[db_name][collection_name]

    def normalize_name(self, name: str) -> str:
        return re.sub(r'\s+', ' ', name.strip().lower())

    def find_all(self):
        try:
            return list(self.collection.find({}, {"_id": 0}))
        except ServerSelectionTimeoutError:
            raise Exception("Could not connect to MongoDB")

    def find_by_name(self, name: str):
        try:
            norm_name = self.normalize_name(name)
            country = self.collection.find_one(
                {"name": {"$regex": f"^{re.escape(name)}$", "$options": "i"}},
                {"_id": 0}
            )
            return country
        except ServerSelectionTimeoutError:
            raise Exception("Could not connect to MongoDB")

    def update_one(self, name: str, update_data: dict):
        try:
            norm_name = self.normalize_name(name)
            country = self.collection.find_one(
                {"name": {"$regex": f"^{re.escape(name)}$", "$options": "i"}}
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

class Country:
    def __init__(self, name, code, population):
        self.name = name
        self.code = code
        self.population = population

    def to_dict(self):
        return {
            "name": self.name,
            "code": self.code,
            "population": self.population
        }