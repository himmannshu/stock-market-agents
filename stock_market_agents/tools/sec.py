"""SEC API tool for fetching financial data."""

import os
import logging
import aiohttp
import json
import asyncio
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SECTool:
    """Tool for interacting with SEC EDGAR database using sec-api.io."""
    
    def __init__(self):
        """Initialize the SEC tool."""
        self.api_key = os.getenv("SEC_API_KEY")
        if not self.api_key:
            raise ValueError("SEC_API_KEY environment variable not set")
        self.base_url = "https://api.sec-api.io"  # Correct base URL
        self.cache = {}  # Simple cache to reduce API calls
        self.cache_ttl = 3600  # Cache TTL in seconds
        self.max_retries = 3  # Maximum number of retries for API calls
        self.retry_delay = 2  # Delay between retries in seconds
        logger.info("Initialized SEC Tool")
        
    async def _make_api_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make an API request with retry logic and error handling.
        
        Args:
            method: HTTP method ('get' or 'post')
            endpoint: API endpoint
            **kwargs: Additional arguments for the request
            
        Returns:
            Response data if successful, None otherwise
        """
        # Ensure the endpoint starts without a slash
        if endpoint.startswith('/'):
            endpoint = endpoint[1:]
        
        # Special handling for the query endpoint
        if endpoint == "query":
            url = "https://api.sec-api.io"
        else:
            url = f"{self.base_url}/{endpoint}"
        
        # Add API key as Authorization header
        headers = {"Authorization": self.api_key}
        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))
            
        logger.debug(f"Making {method.upper()} request to {url}")
            
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    request_method = session.get if method.lower() == 'get' else session.post
                    async with request_method(url, headers=headers, **kwargs) as response:
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 429:  # Rate limit exceeded
                            retry_after = int(response.headers.get('Retry-After', self.retry_delay * 2))
                            logger.warning(f"SEC API rate limit exceeded. Retrying after {retry_after} seconds")
                            await asyncio.sleep(retry_after)
                        elif 500 <= response.status < 600:  # Server error
                            logger.warning(f"SEC API server error {response.status}. Attempt {attempt+1}/{self.max_retries}")
                            await asyncio.sleep(self.retry_delay * (attempt + 1))
                        else:
                            error_text = await response.text()
                            logger.error(f"SEC API request failed with status {response.status}: {error_text}")
                            # For 4xx errors (except rate limiting), don't retry
                            if 400 <= response.status < 500 and response.status != 429:
                                return None
                            await asyncio.sleep(self.retry_delay)
            except aiohttp.ClientError as e:
                logger.error(f"SEC API connection error: {str(e)}")
                await asyncio.sleep(self.retry_delay)
            except Exception as e:
                logger.error(f"Unexpected error in SEC API request: {str(e)}", exc_info=True)
                await asyncio.sleep(self.retry_delay)
                
        logger.error(f"SEC API request to {endpoint} failed after {self.max_retries} attempts")
        return None
    
    async def get_filings(self, ticker: str, form_type: str = "10-K", limit: int = 10) -> Optional[Dict[str, Any]]:
        """Get SEC filings for a company.
        
        Args:
            ticker: Company ticker symbol
            form_type: Type of form to fetch (10-K, 10-Q, 8-K, etc)
            limit: Maximum number of filings to return
            
        Returns:
            Filing data if successful, None otherwise
        """
        try:
            cache_key = f"filings_{ticker}_{form_type}_{limit}"
            if cache_key in self.cache:
                cache_time, cache_data = self.cache[cache_key]
                if datetime.now().timestamp() - cache_time < self.cache_ttl:
                    logger.info(f"Using cached SEC filings for {ticker}")
                    return cache_data
            
            # Build query for filings
            query = {
                "query": {
                    "query_string": {
                        "query": f"ticker:{ticker} AND formType:\"{form_type}\""
                    }
                },
                "from": 0,
                "size": limit,
                "sort": [{"filedAt": {"order": "desc"}}]
            }
            
            logger.info(f"Fetching SEC filings for {ticker} (form {form_type})")
            
            # Make the API request to the query endpoint
            data = await self._make_api_request('post', "query", json=query)
            
            if data:
                # Store in cache
                self.cache[cache_key] = (datetime.now().timestamp(), data)
                logger.info(f"Successfully retrieved SEC filings for {ticker}")
                return data
            
            # Create a minimal fallback for when the API fails
            fallback_data = {
                "filings": [],
                "total": 0,
                "query": str(query)
            }
            self.cache[cache_key] = (datetime.now().timestamp(), fallback_data)
            return fallback_data
                        
        except Exception as e:
            logger.error(f"Failed to fetch SEC filings: {str(e)}", exc_info=True)
            # Return an empty result structure for error handling downstream
            return {"filings": [], "total": 0, "error": str(e)}
    
    async def get_company_facts(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get company facts from SEC.
        
        Args:
            ticker: Company ticker symbol
            
        Returns:
            Company facts if successful, None otherwise
        """
        try:
            cache_key = f"facts_{ticker}"
            if cache_key in self.cache:
                cache_time, cache_data = self.cache[cache_key]
                if datetime.now().timestamp() - cache_time < self.cache_ttl:
                    logger.info(f"Using cached SEC company facts for {ticker}")
                    return cache_data
            
            logger.info(f"Fetching SEC company facts for {ticker}")
            
            # Use the mapping API to get company details instead
            data = await self._make_api_request('get', f"mapping/ticker/{ticker}")
            
            if data:
                # Store in cache
                self.cache[cache_key] = (datetime.now().timestamp(), data)
                return data
            
            # Try CIK lookup as alternative if ticker lookup fails
            logger.info(f"Ticker lookup failed for {ticker}, trying alternative methods")
            
            # Fallback to a more basic structure with essential information
            # This acts as a failsafe when the API doesn't return data
            fallback_data = {
                "name": f"{ticker} Inc.",
                "ticker": ticker,
                "cik": "",
                "exchange": "",
                "industry": "",
                "sector": "",
                "sicCode": "",
                "sicIndustry": "",
                "famaBranchCode": "",
                "famaIndustry": ""
            }
            
            self.cache[cache_key] = (datetime.now().timestamp(), fallback_data)
            return fallback_data
                        
        except Exception as e:
            logger.error(f"Failed to fetch company facts: {str(e)}", exc_info=True)
            # Return a basic fallback structure even on error
            return {
                "name": f"{ticker} Inc.",
                "ticker": ticker,
                "cik": "",
                "error": str(e)
            }
    
    async def get_financial_statements(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get financial statements from SEC filings.
        
        Args:
            ticker: Company ticker symbol
            
        Returns:
            Financial statements if successful, None otherwise
        """
        try:
            cache_key = f"statements_{ticker}"
            if cache_key in self.cache:
                cache_time, cache_data = self.cache[cache_key]
                if datetime.now().timestamp() - cache_time < self.cache_ttl:
                    logger.info(f"Using cached SEC financial statements for {ticker}")
                    return cache_data
            
            # First get the latest 10-K/10-Q filings
            filings = await self.get_filings(ticker, "10-K,10-Q")
            if not filings or "filings" not in filings or not filings["filings"]:
                logger.warning(f"No SEC filings found for {ticker}")
                return None
                
            # Get the latest filing
            latest_filing = filings["filings"][0]
            logger.info(f"Found latest SEC filing for {ticker}: {latest_filing.get('formType')} from {latest_filing.get('filedAt')}")
            
            # Get XBRL data for the filing
            data = await self._make_api_request('get', f"xbrl/{latest_filing['id']}")
            
            if data:
                # Store in cache
                self.cache[cache_key] = (datetime.now().timestamp(), data)
                return data
            
            logger.warning(f"No financial statements found for {ticker}")
            return None
                        
        except Exception as e:
            logger.error(f"Failed to fetch financial statements: {str(e)}", exc_info=True)
            return None
    
    async def get_insider_trading(self, ticker: str, limit: int = 10) -> Optional[Dict[str, Any]]:
        """Get insider trading data for a company.
        
        Args:
            ticker: Company ticker symbol
            limit: Maximum number of transactions to return
            
        Returns:
            Insider trading data if successful, None otherwise
        """
        try:
            cache_key = f"insider_{ticker}_{limit}"
            if cache_key in self.cache:
                cache_time, cache_data = self.cache[cache_key]
                if datetime.now().timestamp() - cache_time < self.cache_ttl:
                    logger.info(f"Using cached SEC insider trading data for {ticker}")
                    return cache_data
            
            logger.info(f"Fetching SEC insider trading data for {ticker}")
            
            # Try to get company CIK first (needed for insider trading data)
            company_data = await self.get_company_facts(ticker)
            
            # Handle the case where company_data is a list (API returns a list of matches)
            if isinstance(company_data, list) and len(company_data) > 0:
                company_data = company_data[0]  # Take the first match
            
            if not company_data or not isinstance(company_data, dict) or not company_data.get('cik'):
                logger.warning(f"Could not get CIK for {ticker}, cannot get insider trading data")
                # Return an empty result structure
                fallback_data = {
                    "transactions": [],
                    "total": 0,
                    "error": f"Could not get CIK for {ticker}"
                }
                self.cache[cache_key] = (datetime.now().timestamp(), fallback_data)
                return fallback_data
            
            # Build query for insider trading
            cik = company_data.get('cik')
            
            # Use the proper SEC-API.io endpoint for Form 4 filings
            query = {
                "query": {
                    "query_string": {
                        "query": f"formType:\"4\" AND issuerCik:{cik}"
                    }
                },
                "from": 0,
                "size": limit,
                "sort": [{"filedAt": {"order": "desc"}}]
            }
            
            logger.info(f"Using CIK {cik} for insider trading query")
            
            # Make the API request to the query endpoint
            data = await self._make_api_request('post', "query", json=query)
            
            if data:
                # Process insider trading data to extract relevant information
                transactions = []
                
                for filing in data.get('filings', []):
                    # Extract basic filing information
                    transaction = {
                        "date": filing.get("filedAt", ""),
                        "name": filing.get("issuerName", ""),
                        "title": filing.get("documentTitleText", ""),
                        "transaction_date": "",
                        "transaction_type": "",
                        "shares": 0,
                        "price": 0.0,
                        "value": 0.0,
                        "link": filing.get("linkToFilingDetails", "")
                    }
                    
                    transactions.append(transaction)
                
                # Create a structured response
                result = {
                    "transactions": transactions,
                    "total": len(transactions),
                    "ticker": ticker,
                    "cik": cik
                }
                
                # Store in cache
                self.cache[cache_key] = (datetime.now().timestamp(), result)
                logger.info(f"Successfully retrieved {len(transactions)} insider transactions for {ticker}")
                return result
            
            # Create a fallback structure for when the API fails
            fallback_data = {
                "transactions": [],
                "total": 0,
                "ticker": ticker,
                "cik": cik or "",
                "query": str(query)
            }
            
            self.cache[cache_key] = (datetime.now().timestamp(), fallback_data)
            logger.warning(f"No insider trading data found for {ticker}")
            return fallback_data
                        
        except Exception as e:
            logger.error(f"Failed to fetch insider trading data: {str(e)}", exc_info=True)
            # Return an empty result structure
            return {
                "transactions": [],
                "total": 0,
                "ticker": ticker,
                "error": str(e)
            }
    
    async def get_key_metrics(self, ticker: str) -> Dict[str, Union[float, str]]:
        """Extract key financial metrics from SEC filings.
        
        Args:
            ticker: Company ticker symbol
            
        Returns:
            Dictionary of key metrics
        """
        try:
            # Get company facts and financial statements
            facts = await self.get_company_facts(ticker)
            statements = await self.get_financial_statements(ticker)
            
            metrics = {
                "ticker": ticker,
                "latest_filing_date": "",
                "revenue_ttm": 0.0,
                "net_income_ttm": 0.0,
                "total_assets": 0.0,
                "total_liabilities": 0.0,
                "total_equity": 0.0,
                "eps_ttm": 0.0,
                "pe_ratio": 0.0,
                "debt_to_equity": 0.0
            }
            
            # Extract data from facts if available
            if facts and "facts" in facts:
                metrics["company_name"] = facts.get("name", ticker)
                
                # Try to get key metrics
                for fact_key, fact_value in facts.get("facts", {}).items():
                    if "Revenues" in fact_key:
                        if isinstance(fact_value, list) and fact_value:
                            metrics["revenue_ttm"] = float(fact_value[0].get("value", 0))
                    elif "NetIncome" in fact_key:
                        if isinstance(fact_value, list) and fact_value:
                            metrics["net_income_ttm"] = float(fact_value[0].get("value", 0))
                    elif "EarningsPerShare" in fact_key:
                        if isinstance(fact_value, list) and fact_value:
                            metrics["eps_ttm"] = float(fact_value[0].get("value", 0))
            
            # Extract data from statements if available
            if statements and "data" in statements:
                statement_data = statements.get("data", {})
                # Get latest financial statement data
                if statement_data.get("BalanceSheet"):
                    metrics["total_assets"] = float(statement_data.get("BalanceSheet", {}).get("Assets", 0))
                    metrics["total_liabilities"] = float(statement_data.get("BalanceSheet", {}).get("Liabilities", 0))
                    metrics["total_equity"] = metrics["total_assets"] - metrics["total_liabilities"]
                    
                    if metrics["total_liabilities"] > 0 and metrics["total_equity"] > 0:
                        metrics["debt_to_equity"] = metrics["total_liabilities"] / metrics["total_equity"]
            
            logger.info(f"Extracted key metrics for {ticker} from SEC data")
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to extract key metrics from SEC data: {str(e)}", exc_info=True)
            return {
                "ticker": ticker,
                "error": str(e)
            }
    
    def clear_cache(self) -> None:
        """Clear the cache."""
        self.cache = {}
        logger.info("SEC Tool cache cleared")
