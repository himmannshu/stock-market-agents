import json
import pytest
import requests
import os
import tempfile
from unittest.mock import Mock, patch
from stock_market_agents.tools.alpha_vantage import AlphaVantageTool, APIEndpoint
from stock_market_agents.utils.cache import Cache
import time

@pytest.fixture
def test_cache_dir():
    """Create a temporary cache directory"""
    temp_dir = tempfile.mkdtemp()
    cache_dir = os.path.join(temp_dir, "cache")
    os.makedirs(cache_dir)
    yield cache_dir
    # Cleanup after test
    try:
        import shutil
        shutil.rmtree(temp_dir)
    except:
        pass

@pytest.fixture
def test_db_dir():
    """Create a temporary db directory"""
    temp_dir = tempfile.mkdtemp()
    db_dir = os.path.join(temp_dir, "db")
    os.makedirs(db_dir)
    yield db_dir
    # Cleanup after test
    try:
        import shutil
        shutil.rmtree(temp_dir)
    except:
        pass

@pytest.fixture
def alpha_vantage_tool(test_cache_dir, test_db_dir, monkeypatch):
    """Create a test instance of AlphaVantageTool"""
    monkeypatch.setattr("stock_market_agents.config.database.CACHE_SETTINGS", {
        "directory": test_cache_dir,
        "default_expiry": 300
    })
    monkeypatch.setattr("stock_market_agents.config.database.DB_SETTINGS", {
        "directory": test_db_dir
    })
    
    # Mock ChromaDB
    mock_collection = Mock()
    mock_collection.count.return_value = 1
    mock_client = Mock()
    mock_client.get_or_create_collection.return_value = mock_collection
    
    with patch("chromadb.Client", return_value=mock_client):
        tool = AlphaVantageTool("test_key")
        tool.collection = mock_collection
        return tool

@pytest.fixture
def mock_alpha_vantage_response():
    """Create a mock Alpha Vantage API response"""
    return {
        "Meta Data": {
            "1. Information": "Daily Prices (open, high, low, close) and Volumes",
            "2. Symbol": "GOOGL",
            "3. Last Refreshed": "2024-03-03",
        },
        "Time Series (Daily)": {
            "2024-03-03": {
                "1. open": "140.0000",
                "2. high": "141.5000",
                "3. low": "139.5000",
                "4. close": "141.0000",
            }
        }
    }

def test_cache_mechanism(alpha_vantage_tool, mock_alpha_vantage_response):
    """Test that the caching mechanism works correctly"""
    # Clear any existing cache first
    cache_key = alpha_vantage_tool._get_cache_key(
        "TIME_SERIES_DAILY",
        {"symbol": "GOOGL"}
    )
    alpha_vantage_tool.cache.delete(cache_key)
    
    # Mock the API call
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = mock_alpha_vantage_response
        mock_get.return_value.status_code = 200

        # First call should hit the API
        result1 = alpha_vantage_tool.make_api_call(
            "TIME_SERIES_DAILY",
            {"symbol": "GOOGL"}
        )
        assert result1 == mock_alpha_vantage_response
        assert mock_get.call_count == 1

        # Second call should use cache
        result2 = alpha_vantage_tool.make_api_call(
            "TIME_SERIES_DAILY",
            {"symbol": "GOOGL"}
        )
        assert result2 == mock_alpha_vantage_response
        assert mock_get.call_count == 1  # Should not have made another API call

def test_query_endpoints(alpha_vantage_tool):
    """Test querying API endpoints"""
    # Mock ChromaDB collection
    mock_results = {
        "ids": [["1"]],
        "distances": [[0.1]],
        "metadatas": [[{
            "name": "TIME_SERIES_DAILY",
            "description": "Daily time series data",
            "endpoint": "function=TIME_SERIES_DAILY",
            "function": "TIME_SERIES_DAILY",
            "required_params": json.dumps({"symbol": "The stock symbol"}),
            "optional_params": json.dumps({"outputsize": "compact|full"})
        }]]
    }
    
    with patch.object(alpha_vantage_tool.collection, "query", return_value=mock_results):
        results = alpha_vantage_tool.query_endpoints("daily")
        assert len(results) > 0
        assert all("daily" in endpoint.description.lower() for endpoint in results)

def test_cache_expiry(alpha_vantage_tool, mock_alpha_vantage_response):
    """Test that cache entries expire correctly"""
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = mock_alpha_vantage_response
        mock_get.return_value.status_code = 200
        
        # Clear any existing cache
        cache_key = alpha_vantage_tool._get_cache_key(
            "TIME_SERIES_DAILY",
            {"symbol": "GOOGL"}
        )
        alpha_vantage_tool.cache.delete(cache_key)
        
        # First call should hit the API
        result1 = alpha_vantage_tool.make_api_call(
            "TIME_SERIES_DAILY",
            {"symbol": "GOOGL"}
        )
        assert result1 == mock_alpha_vantage_response
        assert mock_get.call_count == 1
        
        # Force cache expiry by manipulating the cache file directly
        cache_path = alpha_vantage_tool.cache._get_cache_path(cache_key)
        
        # Read current cache data
        with open(cache_path, 'r') as f:
            cache_data = json.load(f)
        
        # Set expiry to a past time
        cache_data['expiry'] = time.time() - 1
        
        # Write back modified cache data
        with open(cache_path, 'w') as f:
            json.dump(cache_data, f)
        
        # Next call should hit the API again since cache is expired
        result2 = alpha_vantage_tool.make_api_call(
            "TIME_SERIES_DAILY",
            {"symbol": "GOOGL"}
        )
        assert result2 == mock_alpha_vantage_response
        assert mock_get.call_count == 2  # Should have made a second API call

def test_error_handling(alpha_vantage_tool):
    """Test error handling in API calls"""
    with patch("requests.get") as mock_get:
        # Simulate API error
        mock_get.side_effect = requests.RequestException("API Error")
        
        with pytest.raises(requests.RequestException):
            alpha_vantage_tool.make_api_call(
                "TIME_SERIES_DAILY",
                {"symbol": "INVALID"}
            )

def test_cache_key_generation(alpha_vantage_tool):
    """Test cache key generation"""
    key1 = alpha_vantage_tool._get_cache_key(
        "TIME_SERIES_DAILY",
        {"symbol": "GOOGL"}
    )
    key2 = alpha_vantage_tool._get_cache_key(
        "TIME_SERIES_DAILY",
        {"symbol": "AAPL"}
    )
    assert key1 != key2  # Different parameters should generate different keys