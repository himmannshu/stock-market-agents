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
from ..tools.news import WebSearchTool
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
        self.news = WebSearchTool()
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
                    profit_margin=float(overview.get("ProfitMargin", 0)),
                    revenue_growth=float(overview.get("QuarterlyRevenueGrowthYOY", 0)),
                    # Optional fields with default values
                    gross_margin=float(overview.get("GrossMargin", 0)),
                    operating_margin=float(overview.get("OperatingMargin", 0)),
                    description=overview.get("Description", ""),
                    exchange=overview.get("Exchange", ""),
                    peg_ratio=float(overview.get("PEGRatio", 0)),
                    beta=float(overview.get("Beta", 0)),
                    rsi=float(overview.get("RSI", 0)),
                    macd=float(overview.get("MACD", 0)),
                    dividend_yield=float(overview.get("DividendYield", 0)),
                    roe=float(overview.get("ReturnOnEquityTTM", 0)),
                    roa=float(overview.get("ReturnOnAssetsTTM", 0)),
                    debt_to_equity=float(overview.get("DebtToEquityRatio", 0)),
                    current_ratio=float(overview.get("CurrentRatio", 0)),
                    quick_ratio=float(overview.get("QuickRatio", 0))
                )
                
            # Fall back to SEC data if available
            elif sec_data:
                # Handle case where sec_data is a list
                if isinstance(sec_data, list) and len(sec_data) > 0:
                    company_data = sec_data[0]  # Take first company's data
                    return CompanyProfile(
                        name=company_data.get("name", ""),
                        ticker=company_data.get("ticker", ""),
                        sector=company_data.get("sector", ""),
                        industry=company_data.get("industry", ""),
                        market_cap=0,  # Not available in SEC data
                        pe_ratio=0,    # Not available in SEC data
                        profit_margin=0,
                        revenue_growth=0,
                        # Optional fields with default values
                        gross_margin=0,
                        operating_margin=0,
                        description="",
                        exchange="",
                        peg_ratio=0,
                        beta=0,
                        rsi=0,
                        macd=0,
                        dividend_yield=0,
                        roe=0,
                        roa=0,
                        debt_to_equity=0,
                        current_ratio=0,
                        quick_ratio=0
                    )
                # Handle case where sec_data is a dict
                elif isinstance(sec_data, dict):
                    facts = sec_data.get("facts", {})
                    return CompanyProfile(
                        name=facts.get("entityName", ""),
                        ticker=facts.get("tradingSymbol", ""),
                        sector=facts.get("sic", {}).get("industry", ""),
                        industry=facts.get("sic", {}).get("sector", ""),
                        market_cap=0,  # Not available in SEC data
                        pe_ratio=0,    # Not available in SEC data
                        profit_margin=0,
                        revenue_growth=0,
                        # Optional fields with default values
                        gross_margin=0,
                        operating_margin=0,
                        description="",
                        exchange="",
                        peg_ratio=0,
                        beta=0,
                        rsi=0,
                        macd=0,
                        dividend_yield=0,
                        roe=0,
                        roa=0,
                        debt_to_equity=0,
                        current_ratio=0,
                        quick_ratio=0
                    )
                
            # If no data is available, return a minimal profile
            return CompanyProfile(
                name="",
                ticker="",
                sector="",
                industry="",
                market_cap=0,
                pe_ratio=0,
                profit_margin=0,
                revenue_growth=0,
                # Optional fields with default values
                gross_margin=0,
                operating_margin=0,
                description="",
                exchange="",
                peg_ratio=0,
                beta=0,
                rsi=0,
                macd=0,
                dividend_yield=0,
                roe=0,
                roa=0,
                debt_to_equity=0,
                current_ratio=0,
                quick_ratio=0
            )
            
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
        question = question_data.get("question", "")
        company_name = question_data.get("company_name", "")
        ticker = question_data.get("ticker", "")
        metric = question_data.get("metric", "")
        
        logger.info(f"Researching question: {question}")
        logger.info(f"Company: {company_name}, Ticker: {ticker}, Metric: {metric}")
        
        try:
            # If company name is provided but ticker is not, extract the ticker
            if company_name and not ticker:
                company_info = await self.llm.extract_company_info(company_name)
                ticker = company_info.get("ticker", "")
                logger.info(f"Extracted ticker: {ticker}")
            
            # If ticker is not available, try to extract from question
            if not ticker and not company_name:
                company_info = await self.llm.extract_company_info(question)
                company_name = company_info.get("company_name", "")
                ticker = company_info.get("ticker", "")
                logger.info(f"Extracted company: {company_name}, ticker: {ticker}")
            
            # Add validation for ticker to ensure it's valid
            if not ticker:
                logger.warning("No ticker found for research question")
            
            # Find relevant Alpha Vantage endpoints based on the question and metric
            relevant_endpoints = self.alpha_vantage.query_endpoints(question)
            logger.info(f"Found {len(relevant_endpoints)} relevant Alpha Vantage endpoints")
            
            # Get company data from Alpha Vantage using relevant endpoints
            alpha_vantage_data = {}
            alpha_vantage_success = True
            
            try:
                for endpoint in relevant_endpoints:
                    logger.info(f"Fetching data from endpoint: {endpoint.name}")
                    try:
                        # Prepare parameters for the endpoint
                        params = {"symbol": ticker}
                        if endpoint.required_params:
                            for param in endpoint.required_params:
                                if param not in params:
                                    # Add default values for required parameters
                                    if param == "interval":
                                        params[param] = "daily"
                                    elif param == "outputsize":
                                        params[param] = "full"
                                    elif param == "time_period":
                                        params[param] = "14"
                        
                        # Call the endpoint
                        data = await self._call_with_retry(endpoint.function, **params)
                        if data:
                            alpha_vantage_data[endpoint.name] = data
                            self._log_raw_data(data, "alpha_vantage", endpoint.name)
                    except Exception as e:
                        logger.error(f"Failed to fetch data from endpoint {endpoint.name}: {str(e)}")
                        continue
                        
            except Exception as e:
                alpha_vantage_success = False
                logger.error(f"Alpha Vantage API error: {str(e)}. Will try SEC data.")
            
            # Get SEC data regardless of Alpha Vantage success, to supplement information
            sec_data = None
            insider_trading = None
            try:
                logger.info(f"Fetching SEC data for {ticker}")
                sec_data = await self.sec.get_company_facts(ticker)
                if sec_data:
                    logger.info("Successfully retrieved SEC company facts")
                    self._log_raw_data(sec_data, "sec", "company_facts")
                    
                # Also get insider trading data which can be useful
                insider_trading = await self.sec.get_insider_trading(ticker)
                if insider_trading:
                    logger.info("Successfully retrieved SEC insider trading data")
                    self._log_raw_data(insider_trading, "sec", "insider_trading")
            except Exception as e:
                logger.error(f"Failed to get SEC data: {str(e)}")
            
            # Get news data - this should always work even if other APIs fail
            news_articles = []
            if company_name or ticker:
                try:
                    search_term = company_name or ticker
                    logger.info(f"Searching news for {search_term}")
                    news_articles = await self.news.search_company_news(search_term, ticker)
                    if news_articles:
                        logger.info(f"Found {len(news_articles)} news articles")
                        self._log_raw_data(news_articles, "news", "news")
                except Exception as e:
                    logger.error(f"Failed to get news data: {str(e)}")
                    
                # If we still don't have news, try financial metrics search as fallback
                if not news_articles:
                    try:
                        logger.info(f"Trying financial metrics search for {search_term}")
                        financial_data = await self.news.search_financial_metrics(search_term)
                        if financial_data:
                            news_articles = [{"title": "Financial Metrics", "url": "", "summary": json.dumps(financial_data)}]
                            self._log_raw_data(financial_data, "news", "financial_metrics")
                    except Exception as e:
                        logger.error(f"Failed to get financial metrics: {str(e)}")
            
            # Process all available data
            company_profile = self._process_company_profile(alpha_vantage_data.get("OVERVIEW"), sec_data)
            financial_metrics = self._process_financial_metrics(alpha_vantage_data.get("INCOME_STATEMENT"), sec_data)
            balance_sheet = self._process_balance_sheet(alpha_vantage_data.get("BALANCE_SHEET"), sec_data)
            stock_data = self._process_stock_data(alpha_vantage_data.get("TIME_SERIES_DAILY"))
            news_data = NewsData(articles=news_articles) if news_articles else None
            
            # Process any additional data from other endpoints
            additional_metrics = {}
            for endpoint_name, data in alpha_vantage_data.items():
                if endpoint_name not in ["OVERVIEW", "INCOME_STATEMENT", "BALANCE_SHEET", "TIME_SERIES_DAILY"]:
                    try:
                        # Try to extract relevant metrics from the data
                        if "Technical Analysis" in endpoint_name:
                            additional_metrics.update(self._extract_technical_indicators(data))
                        elif "Fundamental Data" in endpoint_name:
                            additional_metrics.update(self._extract_fundamental_data(data))
                        elif "Economic Indicators" in endpoint_name:
                            additional_metrics.update(self._extract_economic_indicators(data))
                    except Exception as e:
                        logger.error(f"Failed to process data from endpoint {endpoint_name}: {str(e)}")
            
            # Ensure we have some data from all sources combined
            if not company_profile and not financial_metrics and not balance_sheet and not stock_data and not news_data and not additional_metrics:
                error_msg = "Failed to retrieve any valid data from available sources"
                logger.error(error_msg)
                return ResearchResults(
                    question=question,
                    company_profile=None,
                    financial_metrics=None,
                    balance_sheet=None,
                    stock_data=None,
                    news_data=news_data,  # Still include news if available
                    error=error_msg
                )
            
            # Create company profile with minimal data if not available
            if not company_profile and (company_name or ticker):
                company_profile = CompanyProfile(
                    name=company_name,
                    ticker=ticker,
                    description="No detailed company information available",
                    sector="",
                    industry="",
                    exchange="",
                    market_cap=0,
                    pe_ratio=0,
                    peg_ratio=0,
                    beta=0,
                    profit_margin=0,
                    revenue_growth=0
                )
            
            # Update company profile with additional metrics if available
            if additional_metrics:
                company_profile = self._update_company_profile(company_profile, additional_metrics)
            
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
            
    def _extract_technical_indicators(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Extract technical indicators from Alpha Vantage data.
        
        Args:
            data: Raw Alpha Vantage data
            
        Returns:
            Dictionary of technical indicators
        """
        indicators = {}
        try:
            # Handle different data formats
            if "Technical Analysis" in data:
                for indicator, values in data["Technical Analysis"].items():
                    if isinstance(values, dict):
                        if "value" in values:
                            indicators[indicator] = float(values["value"])
                        elif "value" in values.get("Technical Analysis", {}):
                            indicators[indicator] = float(values["Technical Analysis"]["value"])
            elif "Technical Indicators" in data:
                for indicator, values in data["Technical Indicators"].items():
                    if isinstance(values, dict):
                        if "value" in values:
                            indicators[indicator] = float(values["value"])
                        elif "value" in values.get("Technical Indicators", {}):
                            indicators[indicator] = float(values["Technical Indicators"]["value"])
            elif "RSI" in data:
                indicators["RSI"] = float(data["RSI"])
            elif "MACD" in data:
                indicators["MACD"] = float(data["MACD"])
            elif "Beta" in data:
                indicators["Beta"] = float(data["Beta"])
            elif "PEG Ratio" in data:
                indicators["PEG Ratio"] = float(data["PEG Ratio"])
            elif "Dividend Yield" in data:
                indicators["Dividend Yield"] = float(data["Dividend Yield"])
            elif "Return on Equity" in data:
                indicators["Return on Equity"] = float(data["Return on Equity"])
            elif "Return on Assets" in data:
                indicators["Return on Assets"] = float(data["Return on Assets"])
            elif "Debt to Equity" in data:
                indicators["Debt to Equity"] = float(data["Debt to Equity"])
            elif "Current Ratio" in data:
                indicators["Current Ratio"] = float(data["Current Ratio"])
            elif "Quick Ratio" in data:
                indicators["Quick Ratio"] = float(data["Quick Ratio"])
        except Exception as e:
            logger.error(f"Failed to extract technical indicators: {str(e)}")
        return indicators
        
    def _extract_fundamental_data(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Extract fundamental data from Alpha Vantage data.
        
        Args:
            data: Raw Alpha Vantage data
            
        Returns:
            Dictionary of fundamental metrics
        """
        metrics = {}
        try:
            # Handle different data formats
            if "Fundamental Data" in data:
                for metric, values in data["Fundamental Data"].items():
                    if isinstance(values, dict):
                        if "value" in values:
                            metrics[metric] = float(values["value"])
                        elif "value" in values.get("Fundamental Data", {}):
                            metrics[metric] = float(values["Fundamental Data"]["value"])
            elif "Overview" in data:
                # Extract metrics from company overview
                overview = data["Overview"]
                if "PERatio" in overview:
                    metrics["PEG Ratio"] = float(overview["PERatio"])
                if "Beta" in overview:
                    metrics["Beta"] = float(overview["Beta"])
                if "DividendYield" in overview:
                    metrics["Dividend Yield"] = float(overview["DividendYield"])
                if "ReturnOnEquityTTM" in overview:
                    metrics["Return on Equity"] = float(overview["ReturnOnEquityTTM"])
                if "ReturnOnAssetsTTM" in overview:
                    metrics["Return on Assets"] = float(overview["ReturnOnAssetsTTM"])
                if "DebtToEquityRatio" in overview:
                    metrics["Debt to Equity"] = float(overview["DebtToEquityRatio"])
                if "CurrentRatio" in overview:
                    metrics["Current Ratio"] = float(overview["CurrentRatio"])
                if "QuickRatio" in overview:
                    metrics["Quick Ratio"] = float(overview["QuickRatio"])
            elif "Income Statement" in data:
                # Extract metrics from income statement
                income = data["Income Statement"]
                if "quarterlyReports" in income and income["quarterlyReports"]:
                    latest = income["quarterlyReports"][0]
                    if "netIncome" in latest and "totalRevenue" in latest:
                        metrics["Profit Margin"] = float(latest["netIncome"]) / float(latest["totalRevenue"])
            elif "Balance Sheet" in data:
                # Extract metrics from balance sheet
                balance = data["Balance Sheet"]
                if "quarterlyReports" in balance and balance["quarterlyReports"]:
                    latest = balance["quarterlyReports"][0]
                    if "totalAssets" in latest and "totalLiabilities" in latest:
                        metrics["Debt to Equity"] = float(latest["totalLiabilities"]) / (float(latest["totalAssets"]) - float(latest["totalLiabilities"]))
        except Exception as e:
            logger.error(f"Failed to extract fundamental data: {str(e)}")
        return metrics
        
    def _extract_economic_indicators(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Extract economic indicators from Alpha Vantage data.
        
        Args:
            data: Raw Alpha Vantage data
            
        Returns:
            Dictionary of economic indicators
        """
        indicators = {}
        try:
            # Handle different data formats
            if "Economic Indicators" in data:
                for indicator, values in data["Economic Indicators"].items():
                    if isinstance(values, dict):
                        if "value" in values:
                            indicators[indicator] = float(values["value"])
                        elif "value" in values.get("Economic Indicators", {}):
                            indicators[indicator] = float(values["Economic Indicators"]["value"])
            elif "Global Quote" in data:
                # Extract market indicators from global quote
                quote = data["Global Quote"]
                if "05. price" in quote:
                    indicators["Current Price"] = float(quote["05. price"])
                if "09. change" in quote:
                    indicators["Price Change"] = float(quote["09. change"])
                if "10. change percent" in quote:
                    indicators["Price Change %"] = float(quote["10. change percent"].strip("%"))
            elif "Time Series (Daily)" in data:
                # Extract market indicators from daily time series
                time_series = data["Time Series (Daily)"]
                if time_series:
                    latest_date = max(time_series.keys())
                    latest_data = time_series[latest_date]
                    if "4. close" in latest_data:
                        indicators["Current Price"] = float(latest_data["4. close"])
                    if "2. high" in latest_data:
                        indicators["Daily High"] = float(latest_data["2. high"])
                    if "3. low" in latest_data:
                        indicators["Daily Low"] = float(latest_data["3. low"])
                    if "5. volume" in latest_data:
                        indicators["Volume"] = float(latest_data["5. volume"])
            elif "Forex (Daily)" in data:
                # Extract forex indicators
                forex = data["Forex (Daily)"]
                if forex:
                    latest_date = max(forex.keys())
                    latest_data = forex[latest_date]
                    if "4. close" in latest_data:
                        indicators["Exchange Rate"] = float(latest_data["4. close"])
            elif "Realtime Currency Exchange Rate" in data:
                # Extract currency exchange rate
                exchange = data["Realtime Currency Exchange Rate"]
                if "5. Exchange Rate" in exchange:
                    indicators["Exchange Rate"] = float(exchange["5. Exchange Rate"])
        except Exception as e:
            logger.error(f"Failed to extract economic indicators: {str(e)}")
        return indicators
        
    def _update_company_profile(self, profile: CompanyProfile, additional_metrics: Dict[str, float]) -> CompanyProfile:
        """Update company profile with additional metrics.
        
        Args:
            profile: Existing company profile
            additional_metrics: Additional metrics to add
            
        Returns:
            Updated company profile
        """
        try:
            # Map additional metrics to profile fields
            metric_mapping = {
                "RSI": "rsi",
                "MACD": "macd",
                "Beta": "beta",
                "PEG Ratio": "peg_ratio",
                "Dividend Yield": "dividend_yield",
                "Return on Equity": "roe",
                "Return on Assets": "roa",
                "Debt to Equity": "debt_to_equity",
                "Current Ratio": "current_ratio",
                "Quick Ratio": "quick_ratio"
            }
            
            # Update profile with available metrics
            for metric, value in additional_metrics.items():
                if metric in metric_mapping:
                    setattr(profile, metric_mapping[metric], value)
                    
            return profile
            
        except Exception as e:
            logger.error(f"Failed to update company profile: {str(e)}")
            return profile

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
