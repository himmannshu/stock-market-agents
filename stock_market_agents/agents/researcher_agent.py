"""ResearcherAgent for gathering financial information"""
import asyncio
import logging
from typing import List, Dict, Any
from .base_agent import BaseAgent
from ..tools.alpha_vantage import AlphaVantageTool
from ..tools.sec_api import SECTool
from ..utils.llm import LLMHelper

logger = logging.getLogger(__name__)

class ResearcherAgent(BaseAgent):
    """Agent responsible for researching financial information"""
    
    def __init__(self, api_key: str):
        """Initialize the researcher agent
        
        Args:
            api_key: Alpha Vantage API key
        """
        super().__init__()
        self.alpha_vantage = AlphaVantageTool(api_key)
        self.sec = SECTool()
        self.llm = LLMHelper()
        logger.info("Initialized ResearcherAgent")
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the researcher agent
        
        Returns:
            System prompt string
        """
        return """You are a financial research agent with access to market data and SEC filings.
Your goal is to gather detailed financial information about companies using available tools.

Follow these steps:
1. Extract relevant company information from questions
2. Use appropriate tools to gather market data and financial statements
3. Handle errors gracefully and try alternative data sources
4. Format financial metrics consistently

Remember to:
- Be thorough in data collection
- Validate data quality
- Handle missing or incomplete data appropriately
- Use proper financial terminology
"""
    
    def _get_available_tools(self) -> List[Dict[str, str]]:
        """Get list of available tools for this agent
        
        Returns:
            List of tool descriptions
        """
        return [
            {
                "name": "query_market_data",
                "description": "Query market data from Alpha Vantage",
                "parameters": {
                    "endpoint": "The Alpha Vantage endpoint to use",
                    "params": "Parameters for the API call"
                }
            },
            {
                "name": "get_sec_data",
                "description": "Get SEC filings data",
                "parameters": {
                    "company": "Company name or ticker",
                    "filing_type": "Type of SEC filing"
                }
            }
        ]
    
    async def research_question(self, question_data: Dict[str, str]) -> Dict[str, Any]:
        """Research a single question using available tools
        
        Args:
            question_data: Dict containing question and optional company info
            
        Returns:
            Research results
        """
        question = question_data["question"]
        company_name = question_data.get("company_name")
        ticker = question_data.get("ticker")
        
        logger.info(f"Researching question: {question}")
        logger.debug(f"Company info - Name: {company_name}, Ticker: {ticker}")
        
        results = {}
        
        try:
            # If no company info provided, try to extract it
            if not company_name and not ticker:
                logger.debug("Extracting company info from question")
                company_info = await self.llm.extract_company_info(question)
                company_name = company_info.get("company_name")
                ticker = company_info.get("ticker")
                logger.info(f"Extracted company info - Name: {company_name}, Ticker: {ticker}")
            
            if not ticker:
                logger.warning("No ticker symbol available, cannot fetch market data")
                return results
            
            # Get market data from Alpha Vantage based on the question
            try:
                logger.debug("Querying Alpha Vantage endpoints")
                
                # Get company overview
                overview = self.alpha_vantage.call_endpoint(
                    "OVERVIEW",
                    symbol=ticker
                )
                results["overview"] = overview
                
                # Get income statement
                income = self.alpha_vantage.call_endpoint(
                    "INCOME_STATEMENT",
                    symbol=ticker
                )
                results["income_statement"] = income
                
                # Get stock performance
                stock = self.alpha_vantage.call_endpoint(
                    "TIME_SERIES_DAILY",
                    symbol=ticker,
                    outputsize="compact"  # Last 100 data points
                )
                results["stock_performance"] = stock
                
                logger.debug("Successfully retrieved market data")
                
            except Exception as e:
                logger.error(f"Failed to get market data: {str(e)}", exc_info=True)
            
            # Get SEC data if company info available
            if company_name or ticker:
                try:
                    logger.debug("Querying SEC data")
                    cik = self.sec.search_company(ticker or company_name)
                    if cik:
                        logger.info(f"Found CIK: {cik}")
                        results["financial_statements"] = self.sec.get_financial_statements(cik)
                        logger.debug("Successfully retrieved SEC data")
                except Exception as e:
                    logger.error(f"Failed to get SEC data: {str(e)}", exc_info=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Research failed: {str(e)}", exc_info=True)
            raise
    
    async def research_multiple(self, questions: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Research multiple questions concurrently
        
        Args:
            questions: List of questions to research
            
        Returns:
            List of research results
        """
        logger.info(f"Starting concurrent research for {len(questions)} questions")
        tasks = [self.research_question(q) for q in questions]
        try:
            results = await asyncio.gather(*tasks)
            logger.info("Completed all research tasks")
            return results
        except Exception as e:
            logger.error(f"Concurrent research failed: {str(e)}", exc_info=True)
            raise
