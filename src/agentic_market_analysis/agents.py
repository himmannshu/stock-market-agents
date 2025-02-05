import re
import requests
import pandas as pd
import os
import yfinance as yf
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from sec_api import QueryApi

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
    Fetch SEC filings for a given target symbol using sec-api.io.
    This function uses a POST request with a query JSON similar to:
    
      {
          "query": "cik:(<CIK>)",
          "from": "0",
          "size": "20",
          "sort": [{ "filedAt": { "order": "desc" } }]
      }
    
    The SEC API token must be set as an environment variable 'SEC_API_TOKEN'.
    The returned filings are summarized and then sentiment is computed using FinBERT.
    """
    sec_api_token = os.environ.get("SEC_API_TOKEN")
    query_fillings = QueryApi(api_key=sec_api_token)
    if not sec_api_token:
        print("SEC_API_TOKEN not set in environment.")
        return pd.DataFrame()
    
    # Build the query JSON based on the sample provided:
    query_json = {
        "query": f"ticker:({target.upper()})",
        "from": "0",
        "size": "5",
        "sort": [{ "filedAt": { "order": "desc" } }]
    }
    
    
    try:
        response = query_fillings.get_filings(query_json)
    except Exception as e:
        print(f"Error fetching SEC filings from sec-api.io for {target}: {e}")
        return pd.DataFrame()
    
    results = []
    filings = response.get("filings", [])
    
    for filing in filings:
        print(filing.get("description"))
        # Extract relevant fields
        company_long = filing.get("companyNameLong", filing.get("companyName", "Unknown Company"))
        form_type = filing.get("formType", "N/A")
        filed_at = filing.get("filedAt", "N/A")
        description = filing.get("description", "")
        
        # Build a summary string for FinBERT analysis
        summary = f"{company_long} filed a {form_type} on {filed_at}. {description}"
        summary = clean_text(summary)
        
        sentiment = finbert_pipeline(summary)[0] if summary else {"label": "NEUTRAL", "score": 0.0}
        
        results.append({
            "source": "SEC Filings",
            "text": summary,
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
