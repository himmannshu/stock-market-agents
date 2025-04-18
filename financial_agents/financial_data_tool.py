import os
import requests
from typing import Any, Dict, List, Optional
import json # For potential JSON embedding later

from agents import function_tool

API_KEY = os.environ.get("FINANCIAL_DATASETS_API_KEY")
BASE_URL = "https://api.financialdatasets.ai"


def _make_request(url: str) -> Dict[str, Any]:
    """Make an authenticated request to the API."""
    if not API_KEY:
        raise ValueError("Financial Datasets API key is not set. Please set the FINANCIAL_DATASETS_API_KEY environment variable.")
    
    headers = {"X-API-KEY": API_KEY}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        error_msg = f"API request failed with status code {response.status_code}: {response.text}"
        # Consider logging the error here as well
        raise Exception(error_msg)

def _get_financial_statements(ticker: str, statement_type: str, period: str = "annual", limit: int = 3) -> Dict[str, Any]:
    """Get financial statements for a company."""
    url = f"{BASE_URL}/financials/{statement_type}?ticker={ticker}&period={period}&limit={limit}"
    return _make_request(url)

def _get_company_metrics(ticker: str, period: str = "annual", limit: int = 3) -> Dict[str, Any]:
    """Get historical financial metrics for a company."""
    url = f"{BASE_URL}/financial-metrics?ticker={ticker}&period={period}&limit={limit}" 
    return _make_request(url)

def _get_stock_prices(ticker: str, interval: str = "1d", limit: int = 90) -> Dict[str, Any]:
    """Get stock price data."""
    url = f"{BASE_URL}/prices?ticker={ticker}&interval={interval}&limit={limit}"
    return _make_request(url)

def _get_company_info(ticker: str) -> Dict[str, Any]:
    """Get general company information."""
    url = f"{BASE_URL}/company?ticker={ticker}"
    return _make_request(url)

def _get_press_releases(ticker: str, limit: int = 1) -> Dict[str, Any]:
    """Get latest earnings press releases."""
    url = f"{BASE_URL}/earnings/press-releases?ticker={ticker}&limit={limit}"
    return _make_request(url)

def _get_segmented_revenues(ticker: str, period: str = "annual", limit: int = 1) -> Dict[str, Any]:
    """Get segmented revenue data."""
    url = f"{BASE_URL}/financials/segmented-revenues?ticker={ticker}&period={period}&limit={limit}"
    return _make_request(url)

def _get_sec_filings(ticker: str, limit: int = 5) -> Dict[str, Any]:
    """Get recent SEC filings."""
    url = f"{BASE_URL}/filings?ticker={ticker}&limit={limit}"
    return _make_request(url)

def _get_company_news(ticker: str, limit: int = 5) -> Dict[str, Any]:
    """Get recent company news."""
    url = f"{BASE_URL}/news?ticker={ticker}&limit={limit}"
    return _make_request(url)

def _get_insider_trades(ticker: str, limit: int = 10) -> Dict[str, Any]:
    """Get recent insider trades."""
    url = f"{BASE_URL}/insider-trades?ticker={ticker}&limit={limit}"
    return _make_request(url)

def _get_institutional_ownership(ticker: str, limit: int = 10) -> Dict[str, Any]:
    """Get institutional ownership data."""
    # Note: The docs show /investor, but the base path seems to be /institutional-ownership
    url = f"{BASE_URL}/institutional-ownership?ticker={ticker}&limit={limit}" 
    return _make_request(url)

def _format_financial_data(data: Dict[str, Any], ticker: str) -> str:
    """Format the retrieved financial data into a detailed Markdown structure."""
    # Initialize the output string
    output = f"## Financial Data Details for {ticker}\n\n"
    
    # News (Top)
    news_data = data.get("company_news")
    if news_data:
        news_list = news_data.get("news", [])
        if news_list:
            output += "\n### Recent News\n\n"
            for news_item in news_list:
                # Avoid potential bolding/italics in titles/sources
                title = news_item.get('title', 'N/A').replace("*", "")
                source = news_item.get('source', 'N/A').replace("*", "")
                output += f"* [{news_item.get('date', 'N/A')}]: {title} ({source})\n"
            output += "\n"
        else:
            output += "\n### Recent News\nNot Available\n\n"
            
    # Company Info
    info = data.get("company_info")
    if info:
        company_data = info.get("company", {}) 
        # Use regular text, not bold for these labels
        output += f"Company: {company_data.get('name', ticker)}\n"
        output += f"Industry: {company_data.get('industry', 'N/A')}\n"
        output += f"Sector: {company_data.get('sector', 'N/A')}\n\n"
    
    # Institutional Ownership
    inst_ownership_data = data.get("institutional_ownership")
    if inst_ownership_data:
        owners = inst_ownership_data.get("institutional_ownership", [])
        if owners:
            output += "\n### Top Institutional Holders\n\n"
            output += "| Holder Name                | Shares Held   | Reported Date |\n"
            output += "|----------------------------|---------------|---------------|\n"
            for owner in owners:
                 # Ensure values don't contain markdown characters that break tables
                 name = str(owner.get('investor_name', 'N/A')).replace("|", "/")
                 shares = str(owner.get('shares_held', 'N/A')).replace("|", "/")
                 date = str(owner.get('report_date', 'N/A')).replace("|", "/")
                 output += f"| {name:<26} | {shares:<13} | {date:<13} |\n"
            output += "\n"
        else:
            output += "\n### Top Institutional Holders\nNot Available\n\n"
            
    # Metrics
    metrics = data.get("metrics")
    if metrics:
        metrics_list = metrics.get("metrics", [])
        if metrics_list:
            output += f"\n### Historical Key Metrics\n\n"
            output += "| Year | Period | Market Cap     | P/E Ratio      | Dividend Yield |\n"
            output += "|------|--------|----------------|----------------|----------------|\n"
            # Iterate through all retrieved metric periods
            for metric_period in metrics_list: 
                 year = str(metric_period.get('year','N/A')).replace("|", "/")
                 period = str(metric_period.get('period','N/A')).replace("|", "/")
                 mcap = str(metric_period.get('marketCap', 'N/A')).replace("|", "/")
                 pe = str(metric_period.get('peRatio', 'N/A')).replace("|", "/")
                 divy = str(metric_period.get('dividendYield', 'N/A')).replace("|", "/")
                 output += f"| {year} | {period:<6} | {mcap:<14} | {pe:<14} | {divy:<14} |\n"
            output += "\n"
        else:
            output += "\n### Key Metrics\nNot Available\n\n"
    
    # Segmented Revenues
    segmented_revenues_data = data.get("segmented_revenues")
    if segmented_revenues_data:
        segments_list = segmented_revenues_data.get("segmented_revenues", [])
        if segments_list:
            latest_segment_report = segments_list[0]
            period_label = f"{latest_segment_report.get('period', 'N/A')} {latest_segment_report.get('report_period', 'N/A')}"
            output += f"\n### Segmented Revenues ({period_label})\n\n"
            
            product_segments = {}
            geo_segments = {}
            other_segments = {}

            for item in latest_segment_report.get("items", []):
                amount = item.get('amount', 0)
                segment_info = item.get("segments", [{}])[0]
                label = segment_info.get("label", "Unknown Segment")
                seg_type = segment_info.get("type", "Unknown Type")
                
                if "Product" in seg_type or "Service" in seg_type:
                    product_segments[label] = amount
                elif "Geographic" in seg_type or "Region" in seg_type or "Countr" in seg_type or "Segment" in seg_type: 
                    geo_segments[label] = amount
                else:
                    other_segments[label] = amount
            
            if product_segments:
                output += "**By Product/Service:**\n"
                output += "| Segment        | Revenue       |\n"
                output += "|----------------|---------------|\n"
                for label, amount in product_segments.items():
                    clean_label = str(label).replace("|", "/")
                    clean_amount = str(amount).replace("|", "/")
                    output += f"| {clean_label:<14} | {clean_amount:<13} |\n" 
                output += "\n"
                output += "\n"
            
            if geo_segments:
                output += "**By Geography/Segment:**\n"
                output += "| Segment        | Revenue       |\n"
                output += "|----------------|---------------|\n"
                for label, amount in geo_segments.items():
                     clean_label = str(label).replace("|", "/")
                     clean_amount = str(amount).replace("|", "/")
                     output += f"| {clean_label:<14} | {clean_amount:<13} |\n"
                output += "\n"
                output += "\n"
            
            if other_segments:
                output += "**By Other Segments:**\n"
                output += "| Segment        | Revenue       |\n"
                output += "|----------------|---------------|\n"
                for label, amount in other_segments.items():
                     clean_label = str(label).replace("|", "/")
                     clean_amount = str(amount).replace("|", "/")
                     output += f"| {clean_label:<14} | {clean_amount:<13} |\n"
                output += "\n"
                output += "\n"
        else:
            output += "\n### Segmented Revenues\nNot Available\n\n"

    # Financial Statements (Income, Balance, Cash Flow)
    income_statements_data = data.get("income_statements")
    if income_statements_data:
        income = income_statements_data.get("income_statements", [])
        if income:
            output += f"\n### Historical Income Statements\n\n"
            output += "| Year | Period | Revenue        | Net Income     | EPS            |\n"
            output += "|------|--------|----------------|----------------|----------------|\n"
            # Iterate through all retrieved income statements
            for statement in income:
                 year = str(statement.get('year','N/A')).replace("|", "/")
                 period = str(statement.get('period','N/A')).replace("|", "/")
                 rev = str(statement.get('revenue', 'N/A')).replace("|", "/")
                 ni = str(statement.get('netIncome', 'N/A')).replace("|", "/")
                 eps = str(statement.get('eps', 'N/A')).replace("|", "/")
                 output += f"| {year} | {period:<6} | {rev:<14} | {ni:<14} | {eps:<14} |\n"
            output += "\n"
        else:
             output += "\n### Income Statements\nNot Available\n\n"
    
    balance_sheets_data = data.get("balance_sheets")
    if balance_sheets_data:
        balance = balance_sheets_data.get("balance_sheets", [])
        if balance:
            output += f"\n### Historical Balance Sheets\n\n"
            output += "| Year | Period | Total Assets   | Total Liab.  | Total Equity   |\n"
            output += "|------|--------|----------------|----------------|----------------|\n"
            # Iterate through all retrieved balance sheets
            for statement in balance:
                 year = str(statement.get('year','N/A')).replace("|", "/")
                 period = str(statement.get('period','N/A')).replace("|", "/")
                 assets = str(statement.get('totalAssets', 'N/A')).replace("|", "/")
                 liab = str(statement.get('totalLiabilities', 'N/A')).replace("|", "/")
                 equity = str(statement.get('totalEquity', 'N/A')).replace("|", "/")
                 output += f"| {year} | {period:<6} | {assets:<14} | {liab:<14} | {equity:<14} |\n"
            output += "\n"
        else:
             output += "\n### Balance Sheets\nNot Available\n\n"
    
    cash_flow_statements_data = data.get("cash_flow_statements")
    if cash_flow_statements_data:
        cash_flow = cash_flow_statements_data.get("cash_flow_statements", [])
        if cash_flow:
            output += f"\n### Historical Cash Flow Statements\n\n"
            output += "| Year | Period | Operating CF   | Investing CF   | Free CF        |\n"
            output += "|------|--------|----------------|----------------|----------------|\n"
            # Iterate through all retrieved cash flow statements
            for statement in cash_flow:
                 year = str(statement.get('year','N/A')).replace("|", "/")
                 period = str(statement.get('period','N/A')).replace("|", "/")
                 ocf = str(statement.get('operatingCashFlow', 'N/A')).replace("|", "/")
                 icf = str(statement.get('investingCashFlow', 'N/A')).replace("|", "/")
                 fcf = str(statement.get('freeCashFlow', 'N/A')).replace("|", "/")
                 output += f"| {year} | {period:<6} | {ocf:<14} | {icf:<14} | {fcf:<14} |\n"
            output += "\n"
        else:
             output += "\n### Cash Flow Statements\nNot Available\n\n"

    # SEC Filings
    sec_filings_data = data.get("sec_filings")
    if sec_filings_data:
        filings = sec_filings_data.get("filings", [])
        if filings:
            output += "\n### Recent SEC Filings\n\n"
            output += "| Date       | Type      | URL                |\n"
            output += "|------------|-----------|--------------------|\n"
            for filing in filings:
                 date = str(filing.get('report_date', 'N/A')).replace("|", "/")
                 type = str(filing.get('filing_type', 'N/A')).replace("|", "/")
                 url = filing.get('url', '#') # URL should be safe
                 output += f"| {date} | {type:<9} | [Link]({url}) |\n"
            output += "\n"
        else:
            output += "\n### Recent SEC Filings\nNot Available\n\n"
             
    # Insider Trades
    insider_trades_data = data.get("insider_trades")
    if insider_trades_data:
        trades = insider_trades_data.get("insider_trades", [])
        if trades:
            output += "\n### Recent Insider Trades\n\n"
            output += "| Date       | Insider Name      | Relationship   | Type | Shares     | Value ($) |\n"
            output += "|------------|-------------------|----------------|------|------------|-----------|\n"
            for trade in trades:
                relationship_raw = str(trade.get('relationship', 'N/A')).replace("|", "/")
                relationship = relationship_raw[:11] + "..." if len(relationship_raw) > 14 else relationship_raw
                
                trans_type = trade.get('transaction_type', 'N/A')
                type_symbol = "?"
                if trans_type == "Acquisition": type_symbol = "A"
                elif trans_type == "Disposition": type_symbol = "D"
                
                date = str(trade.get('date', 'N/A')).replace("|", "/")
                name = str(trade.get('insider_name', 'N/A')).replace("|", "/")
                shares = str(trade.get('shares', 'N/A')).replace("|", "/")
                value = str(trade.get('value', 'N/A')).replace("|", "/")
                
                output += f"| {date} | {name:<17} | {relationship:<14} | {type_symbol:<4} | {shares:<10} | {value:<9} |\n"
            output += "\n"
        else:
            output += "\n### Recent Insider Trades\nNot Available\n\n"
             
    # Stock Price
    prices_data = data.get("prices")
    if prices_data:
        prices = prices_data.get("prices", [])
        if prices:
            output += "\n### Recent Stock Prices (Daily Close)\n\n"
            output += "| Date       | Close Price    |\n"
            output += "|------------|----------------|\n"
            # Show the last 5 prices (or fewer if less data available)
            for price_point in prices[:5]: # Iterate through the first 5 (most recent)
                 date = str(price_point.get('date', 'N/A')).replace("|", "/")
                 close = str(price_point.get('close', 'N/A')).replace("|", "/")
                 output += f"| {date} | {close:<14} |\n"
            output += "\n"
        else:
            output += "\n### Recent Stock Prices\nNot Available\n\n"
            
    # Press Releases
    press_releases_data = data.get("press_releases")
    if press_releases_data:
        releases = press_releases_data.get("press_releases", [])
        if releases:
            latest = releases[0]
            output += "\n### Latest Earnings Press Release\n\n"
            # Avoid potential bolding/italics in title
            title = latest.get('title', 'N/A').replace("*", "")
            output += f"Title: {title}\n"
            output += f"Date: {latest.get('date', 'N/A')}\n\n"
        else:
            output += "\n### Latest Earnings Press Release\nNot Available\n\n"
            
    return output.strip()


@function_tool
async def financial_data_search(ticker: str, 
                                data_type: str, 
                                metrics_period: Optional[str] = None, 
                                metrics_limit: Optional[int] = None,
                                segmented_period: Optional[str] = None,
                                segmented_limit: Optional[int] = None,
                                filings_limit: Optional[int] = None,
                                news_limit: Optional[int] = None,
                                insider_trades_limit: Optional[int] = None,
                                inst_ownership_limit: Optional[int] = None,
                                price_limit: Optional[int] = None) -> str:
    """
    Search for financial data about a company using Financial Datasets API.
    Retrieves various detailed financial data points.
    
    Args:
        ticker: The stock ticker symbol (e.g., AAPL, MSFT, GOOGL). Should be uppercase.
        data_type: Type of data to retrieve (must be one of 'income', 'balance', 'cash-flow', 'metrics', 
                   'prices', 'info', 'press-releases', 'segmented-revenues', 'sec-filings', 'news', 
                   'insider-trades', 'institutional-ownership', or 'all').
        metrics_period: Optional period for historical metrics ('annual' or 'quarterly'). Defaults to 'annual'.
        metrics_limit: Optional limit for historical metrics periods. Defaults to 3.
        segmented_period: Optional period for segmented revenues ('annual' or 'quarterly'). Defaults to 'annual'.
        segmented_limit: Optional limit for segmented revenue periods. Defaults to 1.
        filings_limit: Optional limit for recent SEC filings. Defaults to 5.
        news_limit: Optional limit for recent news articles. Defaults to 5.
        insider_trades_limit: Optional limit for recent insider trades. Defaults to 10.
        inst_ownership_limit: Optional limit for top institutional owners. Defaults to 10.
        price_limit: Optional limit for historical stock prices. Defaults to 90.
        
    Returns:
        Formatted Markdown string containing detailed financial data tables and lists.
    """
    try:
        result = {}
        ticker = ticker.upper() 
        
        valid_data_types = ["income", "balance", "cash-flow", "metrics", "prices", "info", 
                            "press-releases", "segmented-revenues", "sec-filings", "news", 
                            "insider-trades", "institutional-ownership", "all"]
        if data_type not in valid_data_types:
            return f"Error: Invalid data_type '{data_type}'. Must be one of {valid_data_types}"
            
        valid_periods = ["annual", "quarterly"]
        if metrics_period and metrics_period not in valid_periods:
             return f"Error: Invalid metrics_period '{metrics_period}'. Must be one of {valid_periods}"
        if segmented_period and segmented_period not in valid_periods:
             return f"Error: Invalid segmented_period '{segmented_period}'. Must be one of {valid_periods}"

        effective_data_type = data_type if data_type else "all"

        # Fetch data based on data_type
        if effective_data_type in ["info", "all"]:
            result["company_info"] = _get_company_info(ticker)
            
        if effective_data_type in ["news", "all"]:
            limit_to_use = news_limit if news_limit else 5
            result["company_news"] = _get_company_news(ticker, limit=limit_to_use)
            
        if effective_data_type in ["institutional-ownership", "all"]:
            limit_to_use = inst_ownership_limit if inst_ownership_limit else 10
            result["institutional_ownership"] = _get_institutional_ownership(ticker, limit=limit_to_use)
            
        if effective_data_type in ["metrics", "all"]:
            period_to_use = metrics_period if metrics_period else "annual"
            limit_to_use = metrics_limit if metrics_limit else 3
            result["metrics"] = _get_company_metrics(ticker, period=period_to_use, limit=limit_to_use)
            
        if effective_data_type in ["segmented-revenues", "all"]:
            period_to_use = segmented_period if segmented_period else "annual"
            limit_to_use = segmented_limit if segmented_limit else 1
            result["segmented_revenues"] = _get_segmented_revenues(ticker, period=period_to_use, limit=limit_to_use)
            
        if effective_data_type in ["income", "all"]:
            result["income_statements"] = _get_financial_statements(ticker, "income-statements", period="annual", limit=3)
            
        if effective_data_type in ["balance", "all"]:
            result["balance_sheets"] = _get_financial_statements(ticker, "balance-sheets", period="annual", limit=3)
            
        if effective_data_type in ["cash-flow", "all"]:
            result["cash_flow_statements"] = _get_financial_statements(ticker, "cash-flow-statements", period="annual", limit=3)

        if effective_data_type in ["sec-filings", "all"]:
            limit_to_use = filings_limit if filings_limit else 5
            result["sec_filings"] = _get_sec_filings(ticker, limit=limit_to_use)
            
        if effective_data_type in ["insider-trades", "all"]:
            limit_to_use = insider_trades_limit if insider_trades_limit else 10
            result["insider_trades"] = _get_insider_trades(ticker, limit=limit_to_use)

        if effective_data_type in ["prices", "all"]:
            limit_to_use = price_limit if price_limit else 90
            result["prices"] = _get_stock_prices(ticker, limit=limit_to_use)
            
        if effective_data_type in ["press-releases", "all"]:
             result["press_releases"] = _get_press_releases(ticker, limit=1)
        
        return _format_financial_data(result, ticker)
        
    except Exception as e:
        return f"Error retrieving financial data for {ticker}: {str(e)}" 