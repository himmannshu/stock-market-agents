"""SEC API tool for fetching financial data."""

import os
import logging
import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SECTool:
    """Tool for interacting with SEC EDGAR database using sec-api.io."""
    
    def __init__(self):
        """Initialize the SEC tool."""
        self.api_key = os.getenv("SEC_API_KEY")
        if not self.api_key:
            raise ValueError("SEC_API_KEY environment variable not set")
        self.base_url = "https://api.sec-api.io"
        
    async def get_filings(self, ticker: str, form_type: str = "10-K") -> Optional[Dict[str, Any]]:
        """Get SEC filings for a company.
        
        Args:
            ticker: Company ticker symbol
            form_type: Type of form to fetch
            
        Returns:
            Filing data if successful, None otherwise
        """
        try:
            # Calculate date range (last year)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            # Build query
            query = {
                "query": {
                    "query_string": {
                        "query": f"ticker:{ticker} AND formType:\"{form_type}\""
                    }
                },
                "from": "0",
                "size": "10",
                "sort": [{"filedAt": {"order": "desc"}}]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/query",
                    headers={"Authorization": self.api_key},
                    json=query
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        logger.error(f"SEC API request failed: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Failed to fetch SEC filings: {str(e)}", exc_info=True)
            return None
            
    async def get_company_facts(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get company facts from SEC.
        
        Args:
            ticker: Company ticker symbol
            
        Returns:
            Company facts if successful, None otherwise
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/company-facts/{ticker}",
                    headers={"Authorization": self.api_key}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        logger.error(f"SEC API request failed: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Failed to fetch company facts: {str(e)}", exc_info=True)
            return None
            
    async def get_financial_statements(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get financial statements from SEC filings.
        
        Args:
            ticker: Company ticker symbol
            
        Returns:
            Financial statements if successful, None otherwise
        """
        try:
            # First get the latest 10-K/10-Q filings
            filings = await self.get_filings(ticker, "10-K,10-Q")
            if not filings or "filings" not in filings:
                return None
                
            # Get the latest filing
            latest_filing = filings["filings"][0]
            
            # Get XBRL data for the filing
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/xbrl/{latest_filing['id']}",
                    headers={"Authorization": self.api_key}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        logger.error(f"SEC API request failed: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Failed to fetch financial statements: {str(e)}", exc_info=True)
            return None
