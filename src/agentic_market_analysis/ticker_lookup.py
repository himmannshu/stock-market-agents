import os
import requests
from dotenv import load_dotenv

def get_ticker_from_company(company_name: str) -> str:
    """
    Given a company name, use Alpha Vantage's SYMBOL_SEARCH endpoint to return the ticker symbol.
    The API key is expected to be set in the ALPHA_VANTAGE_API_KEY environment variable.
    
    Example endpoint:
    https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords=Apple&apikey=YOUR_API_KEY
    """
    load_dotenv()
    api_key = os.environ.get("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        print("ALPHA_VANTAGE_API_KEY not set in environment.")
        return ""
    
    url = f"https://www.alphavantage.co/query"
    params = {
        "function": "SYMBOL_SEARCH",
        "keywords": company_name,
        "apikey": api_key,
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        best_matches = data.get("bestMatches", [])
        if best_matches:
            # Choose the first match; you could add more logic (e.g., matching region or type)
            ticker = best_matches[0].get("1. symbol", "")
            return ticker
        else:
            print(f"No ticker found for company: {company_name}")
            return ""
    except Exception as e:
        print(f"Error fetching ticker for {company_name}: {e}")
        return ""

# For testing purposes
if __name__ == "__main__":
    company = "Apple"
    ticker = get_ticker_from_company(company)
    print(f"Ticker for {company}: {ticker}")
