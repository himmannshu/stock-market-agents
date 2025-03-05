"""ResearcherAgent for gathering financial information"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd

from ..tools.alpha_vantage import AlphaVantageTool
from ..tools.sec import SECTool
from ..utils.llm import LLMHelper
from ..models.research import (
    CompanyProfile, FinancialMetrics, StockData, 
    BalanceSheet, ResearchResults
)
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class ResearcherAgent(BaseAgent):
    """Agent responsible for researching financial information"""
    
    def __init__(self):
        """Initialize the researcher agent"""
        super().__init__()
        self.alpha_vantage = AlphaVantageTool()
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
- Collect sufficient data for visualization
- Include metadata about data freshness
"""
    
    def _get_available_tools(self) -> List[Dict[str, str]]:
        """Get list of available tools for this agent
        
        Returns:
            List of tool descriptions
        """
        return [
            {
                "name": "extract_companies",
                "description": "Extract company names and tickers from text",
                "parameters": {
                    "text": "Text to extract companies from"
                }
            },
            {
                "name": "get_company_data",
                "description": "Get comprehensive company data",
                "parameters": {
                    "ticker": "Company ticker symbol"
                }
            }
        ]

    def _process_company_profile(self, overview: Dict[str, Any]) -> CompanyProfile:
        """Process company overview data into CompanyProfile.
        
        Args:
            overview: Raw company overview data
            
        Returns:
            Processed CompanyProfile
        """
        try:
            return CompanyProfile(
                name=overview.get("Name", ""),
                ticker=overview.get("Symbol", ""),
                sector=overview.get("Sector", ""),
                industry=overview.get("Industry", ""),
                market_cap=float(overview.get("MarketCapitalization", 0)),
                pe_ratio=float(overview.get("PERatio", 0)),
                gross_margin=float(overview.get("GrossMargin", 0)),
                operating_margin=float(overview.get("OperatingMargin", 0)),
                profit_margin=float(overview.get("ProfitMargin", 0)),
                revenue_growth=float(overview.get("QuarterlyRevenueGrowthYOY", 0))
            )
        except Exception as e:
            logger.error(f"Failed to process company profile: {str(e)}", exc_info=True)
            return None

    def _process_financial_metrics(self, income_statement: Dict[str, Any]) -> FinancialMetrics:
        """Process income statement data into FinancialMetrics.
        
        Args:
            income_statement: Raw income statement data
            
        Returns:
            Processed FinancialMetrics
        """
        try:
            quarterly_reports = income_statement.get("quarterlyReports", [])[:4]
            
            return FinancialMetrics(
                total_revenue=[float(q.get("totalRevenue", 0)) for q in quarterly_reports],
                net_income=[float(q.get("netIncome", 0)) for q in quarterly_reports],
                eps=[float(q.get("reportedEPS", 0)) for q in quarterly_reports],
                periods=[q.get("fiscalDateEnding", "") for q in quarterly_reports]
            )
        except Exception as e:
            logger.error(f"Failed to process financial metrics: {str(e)}", exc_info=True)
            return None

    def _process_balance_sheet(self, balance_sheet: Dict[str, Any]) -> BalanceSheet:
        """Process balance sheet data into BalanceSheet.
        
        Args:
            balance_sheet: Raw balance sheet data
            
        Returns:
            Processed BalanceSheet
        """
        try:
            quarterly_reports = balance_sheet.get("quarterlyReports", [])[:4]
            
            return BalanceSheet(
                total_assets=[float(q.get("totalAssets", 0)) for q in quarterly_reports],
                total_liabilities=[float(q.get("totalLiabilities", 0)) for q in quarterly_reports],
                total_debt=[float(q.get("shortLongTermDebtTotal", 0)) for q in quarterly_reports],
                cash_and_equivalents=[float(q.get("cashAndCashEquivalentsAtCarryingValue", 0)) for q in quarterly_reports],
                periods=[q.get("fiscalDateEnding", "") for q in quarterly_reports]
            )
        except Exception as e:
            logger.error(f"Failed to process balance sheet: {str(e)}", exc_info=True)
            return None

    def _process_stock_data(self, stock_data: Dict[str, Any]) -> StockData:
        """Process stock data into StockData.
        
        Args:
            stock_data: Raw stock data
            
        Returns:
            Processed StockData
        """
        try:
            df = pd.DataFrame(stock_data.get("Time Series (Daily)", {})).T
            df = df.astype(float)
            
            # Calculate metrics
            current_price = float(df.iloc[0]["4. close"])
            high_52week = float(df["2. high"].head(252).max())
            low_52week = float(df["3. low"].head(252).min())
            volume = float(df.iloc[0]["5. volume"])
            
            # Calculate RSI
            delta = df["4. close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # Calculate moving averages
            ma_50 = df["4. close"].rolling(window=50).mean().iloc[-1]
            ma_200 = df["4. close"].rolling(window=200).mean().iloc[-1]
            
            # Calculate beta and volatility
            returns = df["4. close"].pct_change()
            volatility = returns.std() * (252 ** 0.5)  # Annualized
            beta = 1.0  # Placeholder - would need market returns to calculate
            
            # Get historical prices
            historical_prices = df["4. close"].head(30).tolist()
            
            return StockData(
                current_price=current_price,
                high_52week=high_52week,
                low_52week=low_52week,
                volume=volume,
                rsi=float(rsi.iloc[-1]),
                ma_50=float(ma_50),
                ma_200=float(ma_200),
                beta=beta,
                volatility=volatility,
                historical_prices=historical_prices
            )
        except Exception as e:
            logger.error(f"Failed to process stock data: {str(e)}", exc_info=True)
            return None

    async def research_question(self, question_data: Dict[str, str]) -> ResearchResults:
        """Research a single question using available tools.
        
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
        
        try:
            # If no company info provided, try to extract it
            if not company_name and not ticker:
                logger.debug("Extracting company info from question")
                company_info = await self.llm.extract_company_info(question)
                company_name = company_info.get("company_name")
                ticker = company_info.get("ticker")
                logger.info(f"Extracted company info - Name: {company_name}, Ticker: {ticker}")
            
            if not ticker:
                return ResearchResults(
                    question=question,
                    company_profile=None,
                    financial_metrics=None,
                    balance_sheet=None,
                    stock_data=None,
                    error="No ticker symbol available"
                )
            
            # Get market data from Alpha Vantage based on the question
            try:
                logger.debug("Querying Alpha Vantage endpoints")
                
                # Get company overview
                overview = self.alpha_vantage.call_endpoint(
                    "OVERVIEW",
                    symbol=ticker
                )
                company_profile = self._process_company_profile(overview)
                
                # Get income statement
                income = self.alpha_vantage.call_endpoint(
                    "INCOME_STATEMENT",
                    symbol=ticker
                )
                financial_metrics = self._process_financial_metrics(income)
                
                # Get balance sheet
                balance = self.alpha_vantage.call_endpoint(
                    "BALANCE_SHEET",
                    symbol=ticker
                )
                balance_sheet = self._process_balance_sheet(balance)
                
                # Get stock performance (last 365 days)
                stock = self.alpha_vantage.call_endpoint(
                    "TIME_SERIES_DAILY",
                    symbol=ticker,
                    outputsize="full"
                )
                stock_data = self._process_stock_data(stock)
                
                logger.debug("Successfully retrieved market data")
                
                return ResearchResults(
                    question=question,
                    company_profile=company_profile,
                    financial_metrics=financial_metrics,
                    balance_sheet=balance_sheet,
                    stock_data=stock_data
                )
                
            except Exception as e:
                error_msg = f"Failed to get market data: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return ResearchResults(
                    question=question,
                    company_profile=None,
                    financial_metrics=None,
                    balance_sheet=None,
                    stock_data=None,
                    error=error_msg
                )
            
        except Exception as e:
            error_msg = f"Research failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return ResearchResults(
                question=question,
                company_profile=None,
                financial_metrics=None,
                balance_sheet=None,
                stock_data=None,
                error=error_msg
            )

    async def research_concurrent(self, sub_questions: List[Dict[str, str]]) -> List[ResearchResults]:
        """Research multiple questions concurrently.
        
        Args:
            sub_questions: List of questions to research
            
        Returns:
            List of research results
        """
        logger.info(f"Starting concurrent research for {len(sub_questions)} questions")
        
        # Create tasks for each question
        tasks = [
            self.research_question(question)
            for question in sub_questions
        ]
        
        # Run tasks concurrently
        results = await asyncio.gather(*tasks)
        
        logger.info("Completed all research tasks")
        return results
    
    async def research_multiple(self, questions: List[Dict[str, str]]) -> List[ResearchResults]:
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
