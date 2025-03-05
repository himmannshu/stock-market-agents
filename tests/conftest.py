import os
import pytest
from unittest.mock import Mock
from stock_market_agents.tools.alpha_vantage import AlphaVantageTool
from stock_market_agents.agents.researcher_agent import ResearcherAgent
from stock_market_agents.agents.manager_agent import ManagerAgent

@pytest.fixture
def mock_alpha_vantage_response():
    """Mock response for Alpha Vantage API calls"""
    return {
        "Meta Data": {
            "1. Information": "Daily Prices (open, high, low, close) and Volumes",
            "2. Symbol": "GOOGL",
            "3. Last Refreshed": "2024-03-03",
            "4. Output Size": "Compact",
            "5. Time Zone": "US/Eastern"
        },
        "Time Series (Daily)": {
            "2024-03-03": {
                "1. open": "140.0000",
                "2. high": "141.5000",
                "3. low": "139.5000",
                "4. close": "141.0000",
                "5. volume": "1000000"
            }
        }
    }

@pytest.fixture
def mock_alpha_vantage_tool(mock_alpha_vantage_response):
    """Create a mock Alpha Vantage tool"""
    tool = Mock(spec=AlphaVantageTool)
    tool.make_api_call.return_value = mock_alpha_vantage_response
    tool.query_endpoints.return_value = [
        {
            "name": "TIME_SERIES_DAILY",
            "description": "Daily time series of stock prices",
            "endpoint": "function=TIME_SERIES_DAILY",
            "function": "TIME_SERIES_DAILY",
            "required_params": {"symbol": "The stock symbol"},
            "optional_params": {"outputsize": "compact|full"}
        }
    ]
    return tool

@pytest.fixture
def test_cache_dir(tmp_path):
    """Create a temporary directory for cache during tests"""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return str(cache_dir)

@pytest.fixture
def test_db_dir(tmp_path):
    """Create a temporary directory for database during tests"""
    db_dir = tmp_path / "db"
    db_dir.mkdir()
    return str(db_dir)
