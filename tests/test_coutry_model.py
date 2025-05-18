import pytest
from unittest.mock import MagicMock, patch
from app.models.country import CountryModel

@pytest.fixture
def mock_collection():
    return MagicMock()

@pytest.fixture
def country_model(mock_collection):
    with patch("app.models.country.MongoClient") as mock_client:
        mock_client.return_value.__getitem__.return_value.__getitem__.return_value = mock_collection
        yield CountryModel("mongodb://fake", "db", "col")

def test_find_all(country_model, mock_collection):
    mock_collection.find.return_value = [{"name": "South Africa"}]
    result = country_model.find_all()
    assert result == [{"name": "South Africa"}]

def test_find_by_name_found(country_model, mock_collection):
    mock_collection.find_one.return_value = {"name": "South Africa"}
    result = country_model.find_by_name("South Africa")
    assert result == {"name": "South Africa"}

def test_find_by_name_not_found(country_model, mock_collection):
    mock_collection.find_one.return_value = None
    result = country_model.find_by_name("Neverland")
    assert result is None

def test_update_one_success(country_model, mock_collection):
    def find_one_side_effect(*args, **kwargs):
        # Print to debug
        # print("find_one called with:", args, kwargs)
        # First call: find country (no projection)
        if args and args[0].get("name"):
            if not hasattr(find_one_side_effect, "call_count"):
                find_one_side_effect.call_count = 0
            find_one_side_effect.call_count += 1
            if find_one_side_effect.call_count == 1:
                return {"_id": 1, "name": "South Africa"}
            elif find_one_side_effect.call_count == 2:
                return None  # No duplicate name
        # Third call: find by _id with projection
        if args and args[0].get("_id") == 1 and kwargs.get("projection") == {"_id": 0}:
            return {"name": "South Africa", "population": 60_000_000}
        return None

    mock_collection.find_one.side_effect = find_one_side_effect
    mock_collection.update_one.return_value = None
    result = country_model.update_one("South Africa", {"population": 60_000_000})
    assert result == {"name": "South Africa", "population": 60_000_000}

def test_update_one_not_found(country_model, mock_collection):
    mock_collection.find_one.return_value = None
    result = country_model.update_one("Neverland", {"population": 1})
    assert result is None

def test_update_one_duplicate_name(country_model, mock_collection):
    # First find returns the country to update, second find returns a duplicate
    mock_collection.find_one.side_effect = [
        {"_id": 1, "name": "South Africa"},
        {"_id": 2, "name": "Namibia"}
    ]
    with pytest.raises(Exception, match="Country name already exists"):
        country_model.update_one("South Africa", {"name": "Namibia"})