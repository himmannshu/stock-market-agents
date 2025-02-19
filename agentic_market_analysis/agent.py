import re
import json
import pandas as pd
import os
import yfinance as yf
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from sec_api import QueryApi
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

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

def get_stock_data(ticker_symbol: str) -> dict:
    """
    Get stock data for the last 30 days with proper date handling
    """
    ticker = yf.Ticker(ticker_symbol)
    
    try:
        # Get current stock info
        info = ticker.info
        current_price = info.get('regularMarketPrice', 0)
        
        # Set timezone aware dates
        end_date = datetime.now(pytz.UTC)
        start_date = end_date - timedelta(days=30)
        
        # Fetch historical data with interval='1d' for daily data
        hist_data = ticker.history(
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            interval='1d'
        )
        
        if hist_data.empty:
            raise ValueError(f"No historical data found for {ticker_symbol}")
            
        print(f"Historical data range: {hist_data.index[0]} to {hist_data.index[-1]}")
        
        # Calculate price metrics
        price_data = {
            'current_price': current_price,
            'price_history': {
                date.strftime('%Y-%m-%d'): price 
                for date, price in hist_data['Close'].items()
            },
            'dates': [date.strftime('%Y-%m-%d') for date in hist_data.index],
            'prices': hist_data['Close'].tolist(),
            'volumes': hist_data['Volume'].tolist()
        }
        # Calculate changes only if we have enough data
        if len(hist_data) > 1:
            price_data.update({
                'day_change': ((current_price - hist_data['Close'][-1]) / hist_data['Close'][-1] * 100),
                'week_change': ((current_price - hist_data['Close'][-5]) / hist_data['Close'][-5] * 100) if len(hist_data) >= 5 else 0,
                'month_change': ((current_price - hist_data['Close'][0]) / hist_data['Close'][0] * 100),
                'trading_volume': hist_data['Volume'][-1],
                'avg_volume': hist_data['Volume'].mean()
            })

        return price_data
        
    except Exception as e:
        print(f"Error fetching stock data for {ticker_symbol}: {e}")
        return None

def yahoo_finance_agent(target: str) -> pd.DataFrame:
    try:
        # Get stock data first
        stock_data = get_stock_data(target)
        
        if not stock_data:
            return pd.DataFrame()
            
        # Get news data
        ticker = yf.Ticker(target)
        news_list = ticker.news
        #print(news_list)
        results = []
        for item in news_list:
            """
            pub_timestamp = datetime.fromtimestamp(
                item.get("content").get("pubDate")
            ).replace(tzinfo=pytz.UTC)
            print(pub_timestamp)
            # Only include news from the last 30 days
            if pub_timestamp < datetime.now(pytz.UTC) - timedelta(days=30):
                continue
            """
            pub_timestamp = item.get("content").get("pubDate")
            title = item.get("content").get("title", "")
            summary = item.get("content").get("summary", "")
            combined_text = f"{title}. {summary}"
            combined_text = clean_text(combined_text)
            print(combined_text)
            # Find the stock price on the news date
            #news_date = pub_timestamp.strftime('%Y-%m-%d')
            stock_price = stock_data['price_history'].get(stock_data['current_price'])
            #print(stock_price)
            sentiment = finbert_pipeline(combined_text)[0] if combined_text else {"label": "NEUTRAL", "score": 0.0}

            results.append({
                "source": "Yahoo Finance",
                "text": combined_text,
                "sentiment": sentiment,
                "timestamp": pub_timestamp,
                "stock_price": stock_price,
                "current_price": stock_data['current_price'],
                "day_change": stock_data.get('day_change', 0),
                "week_change": stock_data.get('week_change', 0),
                "month_change": stock_data.get('month_change', 0),
                "url": item.get("link", ""),
                "trading_volume": stock_data.get('trading_volume', 0),
                "avg_volume": stock_data.get('avg_volume', 0)
            })
        return pd.DataFrame(results)
        
    except Exception as e:
        print(f"Error in yahoo_finance_agent for {target}: {e}")
        return pd.DataFrame()

def sec_filings_agent(target: str) -> pd.DataFrame:
    load_dotenv()
    sec_api_token = os.environ.get("SEC_API_TOKEN")
    if not sec_api_token:
        print("SEC_API_TOKEN not set")
        return pd.DataFrame()
    
    query_fillings = QueryApi(api_key=sec_api_token)
    query_json = {
        "query": f"ticker:({target.upper()})",
        "from": "0",
        "size": "10",
        "sort": [{ "filedAt": { "order": "desc" } }]
    }
    
    try:
        response = query_fillings.get_filings(query_json)
    except Exception as e:
        print(f"Error fetching SEC filings: {e}")
        return pd.DataFrame()
    
    results = []
    for filing in response.get("filings", []):
        summary = f"{filing.get('companyNameLong', '')} filed a {filing.get('formType', '')} on {filing.get('filedAt', '')}. {filing.get('description', '')}"
        summary = clean_text(summary)
        
        sentiment = finbert_pipeline(summary)[0] if summary else {"label": "NEUTRAL", "score": 0.0}
        
        results.append({
            "source": "SEC Filings",
            "text": summary,
            "sentiment": sentiment,
            "timestamp": pd.to_datetime(filing.get("filedAt")),
            "filing_type": filing.get("formType"),
            "url": filing.get("linkToFilingDetails", "")
        })
    
    return pd.DataFrame(results)
# For testing purposes
if __name__ == "__main__":
    symbol = "AAPL"
    print("Yahoo Finance Agent Results:")
    print(yahoo_finance_agent(symbol))
    
    #print("\nSEC Filings Agent Results:")
    #print(sec_filings_agent(symbol))
