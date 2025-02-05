import re
import requests
import pandas as pd
import os
import yfinance as yf
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

from dotenv import load_dotenv

load_dotenv()

# Initialize FinBERT pipeline from Hugging Face
finbert_model = "yiyanghkust/finbert-tone"
tokenizer = AutoTokenizer.from_pretrained(finbert_model)
model = AutoModelForSequenceClassification.from_pretrained(finbert_model)
finbert_pipeline = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)

def clean_text(text: str) -> str:
    """Basic cleaning to remove HTML tags and extra whitespace."""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def yahoo_finance_agent(target: str) -> pd.DataFrame:
    """
    Fetch news items for a given target symbol from Yahoo Finance using yfinance,
    clean the text, and run FinBERT sentiment analysis.
    """
    ticker = yf.Ticker(target)
    try:
        news_list = ticker.news  # Returns a list of dicts with news items
    except Exception as e:
        print(f"Error fetching Yahoo Finance news for {target}: {e}")
        news_list = []
    
    results = []
    for item in news_list:
        title = item.get("title", "")
        summary = item.get("summary", "")
        combined_text = f"{title}. {summary}"
        combined_text = clean_text(combined_text)
        
        # Use FinBERT to compute sentiment if text is not empty
        sentiment = finbert_pipeline(combined_text)[0] if combined_text else {"label": "NEUTRAL", "score": 0.0}
        
        results.append({
            "source": "Yahoo Finance",
            "text": combined_text,
            "sentiment": sentiment
        })
    
    return pd.DataFrame(results)

def sec_filings_agent(target: str) -> pd.DataFrame:
    """
    Fetch SEC filings using sec-api.io for a given target symbol.
    Requires SEC_API_TOKEN to be set as an environment variable.
    Extracts a simulated text summary from each filing and computes sentiment using FinBERT.
    """
    sec_api_token = os.environ.get("SEC_API_TOKEN")
    if not sec_api_token:
        print("SEC_API_TOKEN not set in environment.")
        return pd.DataFrame()
    
    # Mapping from stock symbol to CIK (extend as needed)
    cik_mapping = {
        "AAPL": "0000320193",
        "MSFT": "0000789019",
        # Add other mappings as required
    }
    cik = cik_mapping.get(target.upper())
    if not cik:
        print(f"No CIK mapping found for symbol {target}")
        return pd.DataFrame()
    
    # Construct the API URL for sec-api.io; adjust parameters per sec-api.io docs.
    # Here, we request the 5 most recent filings for the given CIK.
    url = f"https://api.sec-api.io/v1/filings?token={sec_api_token}&CIK={cik}&limit=5"
    
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"Error fetching SEC filings from sec-api.io for {target}: {e}")
        return pd.DataFrame()
    
    results = []
    # Assume the API returns a JSON object with a "filings" key containing a list of filings.
    filings = data.get("filings", [])
    for filing in filings:
        # Assume each filing has at least 'form' and 'filingDate' keys.
        form_type = filing.get("form", "N/A")
        filing_date = filing.get("filingDate", "N/A")
        # For demonstration, create a simple text summary.
        text = f"SEC Filing {form_type} on {filing_date}."
        text = clean_text(text)
        sentiment = finbert_pipeline(text)[0] if text else {"label": "NEUTRAL", "score": 0.0}
        results.append({
            "source": "SEC Filings",
            "text": text,
            "sentiment": sentiment
        })
    
    return pd.DataFrame(results)

# For testing purposes
if __name__ == "__main__":
    symbol = "AAPL"
    print("Yahoo Finance Agent Results:")
    print(yahoo_finance_agent(symbol))
    
    print("\nSEC Filings Agent Results:")
    print(sec_filings_agent(symbol))
