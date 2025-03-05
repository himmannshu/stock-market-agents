import pytest
from unittest.mock import patch, MagicMock
from stock_market_agents.tools.news import NewsTool
from unittest.mock import AsyncMock

@pytest.fixture
def news_tool():
    with patch.dict('os.environ', {'TAVILY_API_KEY': 'test_key'}):
        return NewsTool()

@pytest.mark.asyncio
async def test_search_company_news_success(news_tool):
    mock_response = {
        "results": [{
            "title": "Test Article",
            "url": "http://test.com",
            "published_date": "2025-03-04",
            "content": "Test content",
            "summary": "Test summary",
            "sentiment": "positive"
        }],
        "answer": "Test analysis"
    }
    
    mock_search = AsyncMock(return_value=mock_response)
    with patch.object(news_tool.client, 'search', mock_search):
        results = await news_tool.search_company_news("Apple", "AAPL")
        
    assert len(results) == 2
    assert results[0]["title"] == "Test Article"
    assert results[1]["type"] == "analysis"

@pytest.mark.asyncio
async def test_search_company_news_error(news_tool):
    mock_search = AsyncMock(side_effect=Exception("API Error"))
    with patch.object(news_tool.client, 'search', mock_search):
        results = await news_tool.search_company_news("Apple", "AAPL")
        
    assert results == []