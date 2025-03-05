import os
import json
import requests
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from ..utils.cache import Cache

logger = logging.getLogger(__name__)

class SECTool:
    """Tool for interacting with the SEC EDGAR API"""
    
    def __init__(self):
        """Initialize the SEC API tool"""
        self.base_url = "https://data.sec.gov/api/xbrl/companyfacts"
        self.submissions_url = "https://data.sec.gov/submissions"
        self.cache = Cache("sec_api")
        
        # SEC API requires a user agent header
        self.headers = {
            "User-Agent": "StockMarketAgents research.bot@example.com",
            "Accept": "application/json"
        }
    
    def get_company_facts(self, cik: str) -> Dict[str, Any]:
        """Get company facts from SEC EDGAR
        
        Args:
            cik: Company CIK number (can include leading zeros)
            
        Returns:
            Company facts data
        """
        # Ensure CIK is 10 digits with leading zeros
        cik = cik.zfill(10)
        cache_key = f"facts_{cik}"
        
        # Try to get from cache first
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            logger.info(f"Cache hit for company facts {cik}")
            return cached_result
        
        # Make API call if not in cache
        url = f"{self.base_url}/CIK{cik}.json"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Cache for 24 hours since this data doesn't change often
            self.cache.set(cache_key, data, expiry=24*3600)
            return data
            
        except requests.RequestException as e:
            logger.error(f"Failed to get company facts: {str(e)}")
            raise
    
    def get_company_filings(self, cik: str) -> Dict[str, Any]:
        """Get company filings from SEC EDGAR
        
        Args:
            cik: Company CIK number (can include leading zeros)
            
        Returns:
            Company filings data
        """
        cik = cik.zfill(10)
        cache_key = f"filings_{cik}"
        
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            logger.info(f"Cache hit for company filings {cik}")
            return cached_result
        
        url = f"{self.submissions_url}/CIK{cik}.json"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Cache for 24 hours
            self.cache.set(cache_key, data, expiry=24*3600)
            return data
            
        except requests.RequestException as e:
            logger.error(f"Failed to get company filings: {str(e)}")
            raise
    
    def get_financial_statements(self, cik: str, filing_type: str = "10-K") -> List[Dict[str, Any]]:
        """Get financial statements from recent filings
        
        Args:
            cik: Company CIK number
            filing_type: Type of filing to get statements from (10-K or 10-Q)
            
        Returns:
            List of financial statements
        """
        filings = self.get_company_filings(cik)
        facts = self.get_company_facts(cik)
        
        # Extract relevant financial data
        financial_data = []
        for concept, data in facts.get("facts", {}).get("us-gaap", {}).items():
            if concept in ["Assets", "Liabilities", "StockholdersEquity", 
                         "Revenues", "NetIncomeLoss", "EarningsPerShareBasic"]:
                for unit_data in data.get("units", {}).values():
                    for entry in unit_data:
                        if entry.get("form") == filing_type:
                            financial_data.append({
                                "concept": concept,
                                "value": entry.get("val"),
                                "period": entry.get("end"),
                                "filing_date": entry.get("filed")
                            })
        
        return financial_data
    
    def search_company(self, query: str) -> Optional[str]:
        """Search for a company CIK by name
        
        Args:
            query: Company name or ticker
            
        Returns:
            CIK number if found, None otherwise
        """
        cache_key = f"search_{query.lower()}"
        
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            logger.info(f"Cache hit for company search {query}")
            return cached_result
        
        # For now, return None as the SEC doesn't provide a direct search API
        # In a real implementation, you would want to use the SEC's EDGAR full-text search
        # or maintain a mapping of company names/tickers to CIK numbers
        return None
