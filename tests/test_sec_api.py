import pytest
import json
import requests
from unittest.mock import Mock, patch
import tempfile
import os
from stock_market_agents.tools.sec_api import SECTool

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
def sec_tool(test_cache_dir, monkeypatch):
    """Create a test instance of SECTool"""
    monkeypatch.setattr("stock_market_agents.config.database.CACHE_SETTINGS", {
        "directory": test_cache_dir,
        "default_expiry": 300
    })
    tool = SECTool()
    # Clear any existing cache
    tool.cache.delete("facts_0000320193")
    return tool

@pytest.fixture
def mock_company_facts():
    """Create mock company facts response"""
    return {
        "cik": "0000320193",
        "entityName": "APPLE INC",
        "facts": {
            "us-gaap": {
                "Assets": {
                    "units": {
                        "USD": [
                            {
                                "val": 1000000,
                                "form": "10-K",
                                "filed": "2024-01-01",
                                "end": "2023-12-31"
                            }
                        ]
                    }
                }
            }
        }
    }

def test_get_company_facts(sec_tool, mock_company_facts):
    """Test getting company facts"""
    with patch("requests.get") as mock_get:
        mock_get.return_value = Mock(
            json=lambda: mock_company_facts,
            status_code=200
        )
        
        # First call should hit the API
        result1 = sec_tool.get_company_facts("320193")
        assert result1 == mock_company_facts
        assert mock_get.call_count == 1
        
        # Second call should use cache
        result2 = sec_tool.get_company_facts("320193")
        assert result2 == mock_company_facts
        assert mock_get.call_count == 1

def test_get_financial_statements(sec_tool, mock_company_facts):
    """Test getting financial statements"""
    with patch("requests.get") as mock_get:
        mock_get.return_value = Mock(
            json=lambda: mock_company_facts,
            status_code=200
        )
        
        statements = sec_tool.get_financial_statements("320193")
        assert len(statements) == 1
        assert statements[0]["concept"] == "Assets"
        assert statements[0]["value"] == 1000000

def test_error_handling(sec_tool):
    """Test error handling"""
    with patch("requests.get") as mock_get:
        mock_get.side_effect = requests.RequestException("API Error")
        
        # Clear cache to force API call
        sec_tool.cache.delete("facts_0000320193")
        
        with pytest.raises(requests.RequestException):
            sec_tool.get_company_facts("320193")
