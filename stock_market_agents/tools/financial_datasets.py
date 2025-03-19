import requests
from dotenv import load_dotenv
import os

load_dotenv()

class FinancialDatasets:
    """Class for managing financial datasets"""
    
    def __init__(self):
        """Initialize the FinancialDatasets class"""
        # Base URL for the Financial Datasets API.
        self.BASE_URL = "https://api.financialdatasets.ai"
        # Your API key for authentication.
        self.API_KEY = os.getenv("FINANCIAL_DATASETS_API_KEY")

    def make_api_call(self, endpoint: str, params: dict) -> dict:
        """
        Helper function to make an API call to the Financial Datasets API.

        Parameters:
            endpoint (str): The API endpoint (path) appended to BASE_URL.
            params (dict): A dictionary of query parameters for the API call.

        Returns:
            dict: The parsed JSON response from the API.

        Raises:
            requests.HTTPError: If the API request fails.
        """
        headers = {"X-API-KEY": self.API_KEY}
        url = f"{self.BASE_URL}{endpoint}"
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_company(self, ticker: str) -> dict:
        """
        Retrieve company data.

        Parameters:
            ticker (str): The company stock ticker symbol.

        Returns:
            dict: Company data as returned by the API.
                Example format: {"company": { ... company details ... }}
        """
        params = {"ticker": ticker}
        return self.make_api_call("/company", params)

    def get_crypto(self, ticker: str) -> dict:
        """
        Retrieve cryptocurrency data.

        Parameters:
            ticker (str): The cryptocurrency ticker symbol.

        Returns:
            dict: Cryptocurrency data as returned by the API.
                Example format: {"crypto": { ... cryptocurrency details ... }}
        """
        params = {"ticker": ticker}
        return self.make_api_call("/crypto", params)

    def get_earnings(self, ticker: str, limit: int = None) -> dict:
        """
        Retrieve earnings data for a given company.

        Parameters:
            ticker (str): The company stock ticker symbol.
            limit (int, optional): The number of earnings records to return.
                                If not provided, the API default will be used.

        Returns:
            dict: Earnings data as returned by the API.
                Example format: {"earnings": [ ... list of earnings records ... ]}
        """
        params = {"ticker": ticker}
        if limit is not None:
            params["limit"] = limit
        return self.make_api_call("/earnings", params)

    def get_financial_metrics(self, ticker: str) -> dict:
        """
        Retrieve financial metrics data.

        Parameters:
            ticker (str): The company stock ticker symbol.

        Returns:
            dict: Financial metrics data as returned by the API.
                Example format: {"metrics": { ... key metrics details ... }}
        """
        params = {"ticker": ticker}
        return self.make_api_call("/financial-metrics", params)

    def get_financial_statements(self, ticker: str, period: str, limit: int) -> dict:
        """
        Retrieve financial statements data (using income statements as the example).

        Parameters:
            ticker (str): The company stock ticker symbol.
            period (str): The period type for the statements. Valid values: 'annual', 'quarterly', 'ttm'.
            limit (int): The number of statement records to return.

        Returns:
            dict: Financial statements data as returned by the API.
                Example format: {"income_statements": [ ... list of statements ... ]}
        """
        params = {"ticker": ticker, "period": period, "limit": limit}
        return self.make_api_call("/financials/income-statements", params)

    def get_insider_trades(self, ticker: str) -> dict:
        """
        Retrieve insider trades data.

        Parameters:
            ticker (str): The company stock ticker symbol.

        Returns:
            dict: Insider trades data as returned by the API.
                Example format: {"insider_trades": [ ... list of insider trades ... ]}
        """
        params = {"ticker": ticker}
        return self.make_api_call("/insider-trades", params)

    def get_institutional_ownership(self, ticker: str) -> dict:
        """
        Retrieve institutional ownership data.

        Parameters:
            ticker (str): The company stock ticker symbol.

        Returns:
            dict: Institutional ownership data as returned by the API.
                Example format: {"institutional_ownership": [ ... list of institutional records ... ]}
        """
        params = {"ticker": ticker}
        return self.make_api_call("/institutional-ownership", params)

    def get_news(self, ticker: str) -> dict:
        """
        Retrieve market news data, optionally filtered by a company's ticker.

        Parameters:
            ticker (str): The company stock ticker symbol to filter news.
                        (If the API supports global news, this parameter might be optional.)

        Returns:
            dict: News data as returned by the API.
                Example format: {"news": [ ... list of news articles ... ]}
        """
        params = {"ticker": ticker}
        return self.make_api_call("/news", params)

    def get_prices(self, ticker: str) -> dict:
        """
        Retrieve stock price data.

        Parameters:
            ticker (str): The company stock ticker symbol.

        Returns:
            dict: Stock price data as returned by the API.
                Example format: {"prices": { ... price details ... }}
        """
        params = {"ticker": ticker}
        return self.make_api_call("/prices", params)

    def search(self, query: str) -> dict:
        """
        Search across available financial datasets.

        Parameters:
            query (str): The search query string.

        Returns:
            dict: Search results as returned by the API.
                Example format: {"results": [ ... list of matching records ... ]}
        """
        params = {"query": query}
        return self.make_api_call("/search", params)

    def get_sec_filings(self, ticker: str) -> dict:
        """
        Retrieve SEC filings data.

        Parameters:
            ticker (str): The company stock ticker symbol.

        Returns:
            dict: SEC filings data as returned by the API.
                Example format: {"sec_filings": [ ... list of filings ... ]}
        """
        params = {"ticker": ticker}
        return self.make_api_call("/sec-filings", params)

    def get_segmented_financials(self, ticker: str) -> dict:
        """
        Retrieve segmented financials data.

        Parameters:
            ticker (str): The company stock ticker symbol.

        Returns:
            dict: Segmented financials data as returned by the API.
                Example format: {"segmented_financials": [ ... list of segmented financial details ... ]}
        """
        params = {"ticker": ticker}
        return self.make_api_call("/segmented-financials", params)
