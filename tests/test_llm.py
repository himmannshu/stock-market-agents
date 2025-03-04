import pytest
from unittest.mock import AsyncMock, patch, Mock
import json
from stock_market_agents.utils.llm import LLMHelper

@pytest.fixture
def llm_helper():
    """Create a test instance of LLMHelper"""
    return LLMHelper("test-key")

@pytest.mark.asyncio
async def test_break_down_question(llm_helper):
    """Test breaking down a complex question"""
    mock_response = Mock(
        choices=[
            Mock(
                message=Mock(
                    content=json.dumps([
                        {
                            "question": "What is Apple's current P/E ratio?",
                            "company_name": "Apple",
                            "ticker": "AAPL"
                        },
                        {
                            "question": "How does this compare to industry average?",
                            "company_name": None,
                            "ticker": None
                        }
                    ])
                )
            )
        ]
    )
    
    with patch.object(llm_helper.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response
        
        result = await llm_helper.break_down_question(
            "How does Apple's P/E ratio compare to the industry average?"
        )
        
        assert len(result) == 2
        assert result[0]["company_name"] == "Apple"
        assert result[0]["ticker"] == "AAPL"
        assert "P/E ratio" in result[0]["question"]

@pytest.mark.asyncio
async def test_extract_company_info(llm_helper):
    """Test extracting company info from text"""
    mock_response = Mock(
        choices=[
            Mock(
                message=Mock(
                    content=json.dumps({
                        "company_name": "Apple Inc.",
                        "ticker": "AAPL"
                    })
                )
            )
        ]
    )
    
    with patch.object(llm_helper.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response
        
        result = await llm_helper.extract_company_info(
            "What is Apple's current stock price?"
        )
        
        assert result["company_name"] == "Apple Inc."
        assert result["ticker"] == "AAPL"

@pytest.mark.asyncio
async def test_analyze_results(llm_helper):
    """Test analyzing research results"""
    mock_response = Mock(
        choices=[
            Mock(
                message=Mock(
                    content=json.dumps({
                        "summary": "Apple's P/E ratio is above industry average",
                        "detailed_analysis": "Analysis details...",
                        "confidence": 0.85,
                        "limitations": ["Limited historical data"],
                        "sources": ["Alpha Vantage", "SEC Filings"]
                    })
                )
            )
        ]
    )
    
    with patch.object(llm_helper.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response
        
        result = await llm_helper.analyze_results(
            "How does Apple's P/E ratio compare to the industry average?",
            [{"question": "What is Apple's P/E ratio?"}],
            [{"market_data": {"pe_ratio": 25.5}}]
        )
        
        assert result["confidence"] > 0.8
        assert "Apple" in result["summary"]
        assert len(result["limitations"]) > 0
        assert len(result["sources"]) > 0

@pytest.mark.asyncio
async def test_error_handling(llm_helper):
    """Test error handling in LLM helper"""
    with patch.object(llm_helper.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.side_effect = Exception("API Error")
        
        # Test break_down_question error handling
        result = await llm_helper.break_down_question("Test question")
        assert len(result) == 1
        assert result[0]["question"] == "Test question"
        
        # Test extract_company_info error handling
        result = await llm_helper.extract_company_info("Test text")
        assert result["company_name"] is None
        assert result["ticker"] is None
        
        # Test analyze_results error handling
        result = await llm_helper.analyze_results("Test", [], [])
        assert result["confidence"] == 0.0
        assert "failed" in result["summary"].lower()
