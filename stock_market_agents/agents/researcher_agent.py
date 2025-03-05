"""ResearcherAgent for gathering financial information"""
import asyncio
import logging
import time
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd

from ..tools.alpha_vantage import AlphaVantageTool
from ..tools.sec import SECTool
from ..tools.news import NewsTool
from ..utils.llm import LLMHelper
from ..models.research import (
    CompanyProfile, FinancialMetrics, StockData, 
    BalanceSheet, ResearchResults, NewsData
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
        self.news = NewsTool()
        self.llm = LLMHelper()
        self.rate_limit_delay = 60  # Delay in seconds when rate limited
        self.max_retries = 3
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
    
    async def _call_with_retry(self, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Call an Alpha Vantage endpoint with retry logic.
        
        Args:
            endpoint: Endpoint to call
            **kwargs: Additional arguments for the endpoint
            
        Returns:
            Response data or None if all retries fail
        """
        for attempt in range(self.max_retries):
            try:
                data = self.alpha_vantage.call_endpoint(endpoint, **kwargs)
                if data and "Note" not in data:  # "Note" indicates rate limit
                    return data
                    
                # If rate limited, wait and retry
                logger.warning(f"Rate limited on attempt {attempt + 1}, waiting {self.rate_limit_delay}s")
                await asyncio.sleep(self.rate_limit_delay)
                self.rate_limit_delay *= 2  # Exponential backoff
                
            except Exception as e:
                logger.error(f"API call failed on attempt {attempt + 1}: {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1)  # Brief delay between retries
                    
        return None
    
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

    def _log_raw_data(self, data: Dict[str, Any], source: str, data_type: str) -> None:
        """Log raw data for debugging and analysis.
        
        Args:
            data: Raw data to log
            source: Data source (e.g. 'alpha_vantage', 'sec')
            data_type: Type of data (e.g. 'overview', 'income')
        """
        try:
            # Format data for logging
            formatted = json.dumps(data, indent=2)
            logger.info(f"Raw {source} {data_type} data:\n{formatted}")
        except Exception as e:
            logger.error(f"Failed to log raw data: {str(e)}")
    
    def _process_company_profile(self, overview: Dict[str, Any], sec_data: Optional[Dict[str, Any]] = None) -> CompanyProfile:
        """Process company overview data into CompanyProfile.
        
        Args:
            overview: Raw company overview data
            sec_data: Optional SEC data as backup
            
        Returns:
            Processed CompanyProfile
        """
        try:
            # Try Alpha Vantage data first
            if overview:
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
                
            # Fall back to SEC data if available
            elif sec_data:
                facts = sec_data.get("facts", {})
                return CompanyProfile(
                    name=facts.get("entityName", ""),
                    ticker=facts.get("tradingSymbol", ""),
                    sector=facts.get("sic", {}).get("industry", ""),
                    industry=facts.get("sic", {}).get("sector", ""),
                    market_cap=0,  # Not available in SEC data
                    pe_ratio=0,    # Not available in SEC data
                    gross_margin=0, # Would need to calculate from financial statements
                    operating_margin=0,
                    profit_margin=0,
                    revenue_growth=0
                )
                
            return None
            
        except Exception as e:
            logger.error(f"Failed to process company profile: {str(e)}", exc_info=True)
            return None

    def _process_financial_metrics(self, income_statement: Dict[str, Any], sec_data: Optional[Dict[str, Any]] = None) -> FinancialMetrics:
        """Process income statement data into FinancialMetrics.
        
        Args:
            income_statement: Raw income statement data
            sec_data: Optional SEC data as backup
            
        Returns:
            Processed FinancialMetrics
        """
        try:
            # Try Alpha Vantage data first
            if income_statement:
                quarterly_reports = income_statement.get("quarterlyReports", [])[:4]
                return FinancialMetrics(
                    total_revenue=[float(q.get("totalRevenue", 0)) for q in quarterly_reports],
                    net_income=[float(q.get("netIncome", 0)) for q in quarterly_reports],
                    eps=[float(q.get("reportedEPS", 0)) for q in quarterly_reports],
                    periods=[q.get("fiscalDateEnding", "") for q in quarterly_reports]
                )
                
            # Fall back to SEC data if available
            elif sec_data and "financialStatements" in sec_data:
                statements = sec_data["financialStatements"]
                return FinancialMetrics(
                    total_revenue=[float(q.get("revenue", 0)) for q in statements[:4]],
                    net_income=[float(q.get("netIncome", 0)) for q in statements[:4]],
                    eps=[float(q.get("eps", 0)) for q in statements[:4]],
                    periods=[q.get("periodEnd", "") for q in statements[:4]]
                )
                
            return None
            
        except Exception as e:
            logger.error(f"Failed to process financial metrics: {str(e)}", exc_info=True)
            return None

    def _process_balance_sheet(self, balance_sheet: Dict[str, Any], sec_data: Optional[Dict[str, Any]] = None) -> BalanceSheet:
        """Process balance sheet data into BalanceSheet.
        
        Args:
            balance_sheet: Raw balance sheet data
            sec_data: Optional SEC data as backup
            
        Returns:
            Processed BalanceSheet
        """
        try:
            # Try Alpha Vantage data first
            if balance_sheet:
                quarterly_reports = balance_sheet.get("quarterlyReports", [])[:4]
                return BalanceSheet(
                    total_assets=[float(q.get("totalAssets", 0)) for q in quarterly_reports],
                    total_liabilities=[float(q.get("totalLiabilities", 0)) for q in quarterly_reports],
                    total_debt=[float(q.get("shortLongTermDebtTotal", 0)) for q in quarterly_reports],
                    cash_and_equivalents=[float(q.get("cashAndCashEquivalentsAtCarryingValue", 0)) for q in quarterly_reports],
                    periods=[q.get("fiscalDateEnding", "") for q in quarterly_reports]
                )
                
            # Fall back to SEC data if available
            elif sec_data and "financialStatements" in sec_data:
                statements = sec_data["financialStatements"]
                return BalanceSheet(
                    total_assets=[float(q.get("totalAssets", 0)) for q in statements[:4]],
                    total_liabilities=[float(q.get("totalLiabilities", 0)) for q in statements[:4]],
                    total_debt=[float(q.get("totalDebt", 0)) for q in statements[:4]],
                    cash_and_equivalents=[float(q.get("cashAndEquivalents", 0)) for q in statements[:4]],
                    periods=[q.get("periodEnd", "") for q in statements[:4]]
                )
                
            return None
            
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
            if not stock_data or "Time Series (Daily)" not in stock_data:
                return None
                
            df = pd.DataFrame(stock_data["Time Series (Daily)"]).T
            if df.empty:
                return None
                
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
                    news_data=None,
                    error="No ticker symbol available"
                )
            
            # Try Alpha Vantage first
            logger.debug("Querying Alpha Vantage endpoints")
            overview = await self._call_with_retry("OVERVIEW", symbol=ticker)
            income = await self._call_with_retry("INCOME_STATEMENT", symbol=ticker)
            balance = await self._call_with_retry("BALANCE_SHEET", symbol=ticker)
            stock = await self._call_with_retry("TIME_SERIES_DAILY", symbol=ticker, outputsize="full")
            
            # Log raw Alpha Vantage data
            if overview:
                self._log_raw_data(overview, "alpha_vantage", "overview")
            if income:
                self._log_raw_data(income, "alpha_vantage", "income")
            if balance:
                self._log_raw_data(balance, "alpha_vantage", "balance")
            if stock:
                self._log_raw_data(stock, "alpha_vantage", "stock")
            
            # If Alpha Vantage fails, try SEC data
            sec_data = None
            if not overview or not income or not balance:
                logger.info("Alpha Vantage data incomplete, trying SEC data")
                try:
                    sec_data = await self.sec.get_company_facts(ticker)
                    if sec_data:
                        logger.info("Successfully retrieved SEC data")
                        self._log_raw_data(sec_data, "sec", "company_facts")
                except Exception as e:
                    logger.error(f"Failed to get SEC data: {str(e)}")
            
            # Get news data
            news_articles = []
            if company_name:
                try:
                    news_articles = await self.news.search_company_news(company_name, ticker)
                    if news_articles:
                        self._log_raw_data(news_articles, "tavily", "news")
                except Exception as e:
                    logger.error(f"Failed to get news data: {str(e)}")
            
            # Process all available data
            company_profile = self._process_company_profile(overview, sec_data)
            financial_metrics = self._process_financial_metrics(income, sec_data)
            balance_sheet = self._process_balance_sheet(balance, sec_data)
            stock_data = self._process_stock_data(stock) if stock else None
            news_data = NewsData(articles=news_articles) if news_articles else None
            
            if not any([company_profile, financial_metrics, balance_sheet, stock_data, news_data]):
                error_msg = "Failed to retrieve any valid data from available sources"
                logger.error(error_msg)
                return ResearchResults(
                    question=question,
                    company_profile=None,
                    financial_metrics=None,
                    balance_sheet=None,
                    stock_data=None,
                    news_data=None,
                    error=error_msg
                )
            
            logger.info("Successfully processed research data")
            return ResearchResults(
                question=question,
                company_profile=company_profile,
                financial_metrics=financial_metrics,
                balance_sheet=balance_sheet,
                stock_data=stock_data,
                news_data=news_data
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
                news_data=None,
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
