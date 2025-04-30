import os
import requests
from typing import Any, Dict, List, Optional
import json # For potential JSON embedding later
from datetime import datetime, timedelta # Added import
import math # For number formatting

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

def _get_stock_prices(ticker: str, interval: str, interval_multiplier: int, start_date: str, end_date: str, limit: Optional[int] = None) -> Dict[str, Any]:
    """Get stock price data."""
    # Build the base URL
    url = f"{BASE_URL}/prices?ticker={ticker}&interval={interval}&interval_multiplier={interval_multiplier}&start_date={start_date}&end_date={end_date}"
    
    # Add limit only if provided
    if limit is not None:
        url += f"&limit={limit}"
        
    return _make_request(url)

def _get_company_info(ticker: str) -> Dict[str, Any]:
    """Get general company information."""
    url = f"{BASE_URL}/company/facts?ticker={ticker}"
    return _make_request(url)

def _get_press_releases(ticker: str, limit: int = 1) -> Dict[str, Any]:
    """Get latest earnings press releases."""
    url = f"{BASE_URL}/earnings/press-releases?ticker={ticker}"
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

def _format_number(num):
    """Formats large numbers into readable strings (e.g., 1.23B, 456.7M, 89.1K)."""
    if num is None or not isinstance(num, (int, float)):
        return 'N/A'
    if abs(num) < 1000:
        # Handle potential floats with 2 decimal places, but ints as ints
        return f"{num:.2f}" if isinstance(num, float) else str(num)
        
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
        
    # Determine suffix based on magnitude
    suffix = ['', 'K', 'M', 'B', 'T'][magnitude]
    
    # Format with 2 decimal places and add suffix
    return f'{num:.2f}{suffix}'

def _get_year_from_date(date_str):
    """Safely extracts the year from a YYYY-MM-DD string."""
    if date_str and isinstance(date_str, str) and len(date_str) >= 4:
        return date_str[:4]
    return 'N/A'

def _get_date_from_datetime(datetime_str):
    """Safely extracts the date (YYYY-MM-DD) from an ISO datetime string."""
    if datetime_str and isinstance(datetime_str, str) and len(datetime_str) >= 10:
        return datetime_str[:10]
    return 'N/A'

def _format_financial_data(data: Dict[str, Any], ticker: str) -> str:
    """Format the retrieved financial data into a detailed Markdown structure."""
    output = f"## Financial Data Details for {ticker}\n\n"
    
    # News (Top) - Assuming this part is correct as per user feedback
    news_data = data.get("company_news")
    if news_data:
        news_list = news_data.get("news", [])
        if news_list:
            output += "\n### Recent News\n\n"
            for news_item in news_list:
                title = str(news_item.get('title', 'N/A')).replace("*", "")
                source = str(news_item.get('source', 'N/A')).replace("*", "")
                date_str = _get_date_from_datetime(news_item.get('date', 'N/A'))
                url = news_item.get('url', '#')
                output += f"* [{date_str}]: [{title}]({url}) ({source})\n"
            output += "\n"
        else:
            output += "\n### Recent News\nNot Available\n\n"
            
    # Company Info
    info_data = data.get("company_info")
    if info_data:
        company_facts = info_data.get("company_facts", {}) # Use company_facts key
        output += f"Company: {company_facts.get('name', ticker)}\n" # Use name from facts
        output += f"Industry: {company_facts.get('industry', 'N/A')}\n"
        output += f"Sector: {company_facts.get('sector', 'N/A')}\n\n"
    
    # Institutional Ownership
    inst_ownership_data = data.get("institutional_ownership")
    if inst_ownership_data:
         # Access the list correctly
        owners = inst_ownership_data.get("institutional_ownership", [])
        if owners:
            output += "\n### Top Institutional Holders\n\n"
            output += "| Holder Name                | Shares Held   | Reported Date |\n"
            output += "|----------------------------|---------------|---------------|\n"
            for owner in owners:
                 # Use correct keys from JSON
                 name = str(owner.get('investor', 'N/A')).replace("|", "/")
                 shares = _format_number(owner.get('shares')) # Format shares
                 date = str(owner.get('report_period', 'N/A')).replace("|", "/")
                 output += f"| {name:<26} | {shares:<13} | {date:<13} |\n"
            output += "\n"
        else:
            output += "\n### Top Institutional Holders\nNot Available\n\n"
            
    # Metrics
    metrics_data = data.get("metrics")
    if metrics_data:
        # Access the list correctly
        metrics_list = metrics_data.get("financial_metrics", []) 
        if metrics_list:
            output += f"\n### Historical Key Metrics\n\n"
            output += "| Year | Period | Market Cap     | P/E Ratio      | Dividend Yield |\n"
            output += "|------|--------|----------------|----------------|----------------|\n"
            for metric_period in metrics_list: 
                 # Use correct keys and helper
                 year = _get_year_from_date(metric_period.get('report_period'))
                 period = str(metric_period.get('period','N/A')).replace("|", "/")
                 mcap = _format_number(metric_period.get('market_cap'))
                 pe = f"{metric_period.get('price_to_earnings_ratio', 'N/A'):.2f}" if metric_period.get('price_to_earnings_ratio') is not None else 'N/A'
                 # Assuming dividend_yield key exists, format it; otherwise N/A
                 divy_raw = metric_period.get('dividend_yield') 
                 divy = f"{divy_raw:.2%}" if divy_raw is not None else 'N/A' 
                 output += f"| {year} | {period:<6} | {mcap:<14} | {pe:<14} | {divy:<14} |\n"
            output += "\n"
        else:
            output += "\n### Key Metrics\nNot Available\n\n"
    
    # Segmented Revenues - Simplified Logic
    segmented_revenues_data = data.get("segmented_revenues")
    if segmented_revenues_data:
        segments_reports = segmented_revenues_data.get("segmented_revenues", [])
        if segments_reports:
            latest_report = segments_reports[0] # Process only the latest report period
            report_period_label = f"{latest_report.get('period', 'N/A')} {latest_report.get('report_period', 'N/A')}"
            output += f"\n### Segmented Revenues ({report_period_label})\n\n"
            
            revenue_items = []
            for item in latest_report.get("items", []):
                # Filter specifically for revenue items and ensure segments exist
                if 'Revenue' in item.get('name', '') and item.get('segments'): 
                    segment_info = item['segments'][0] # Assume first segment is primary
                    label = segment_info.get("label", "Unknown Segment")
                    amount = item.get('amount')
                    # Avoid adding items with no amount
                    if amount is not None:
                         revenue_items.append({'label': label, 'amount': amount})
            
            if revenue_items:
                output += "| Segment                     | Revenue       |\n"
                output += "|---------------------------|---------------|\n"
                # Sort by amount descending for clarity
                revenue_items.sort(key=lambda x: x['amount'], reverse=True)
                for item in revenue_items:
                     clean_label = str(item['label']).replace("|", "/")
                     clean_amount = _format_number(item['amount'])
                     output += f"| {clean_label:<25} | {clean_amount:<13} |\n"
                output += "\n"
            else:
                 output += "Segment revenue data not available or not in expected format.\n\n"
        else:
            output += "\n### Segmented Revenues\nNot Available\n\n"

    # Financial Statements (Income)
    income_statements_data = data.get("income_statements")
    if income_statements_data:
        income_list = income_statements_data.get("income_statements", [])
        if income_list:
            output += f"\n### Historical Income Statements\n\n"
            output += "| Year | Period | Revenue        | Net Income     | EPS Diluted    |\n"
            output += "|------|--------|----------------|----------------|----------------|\n"
            for statement in income_list:
                 year = _get_year_from_date(statement.get('report_period'))
                 period = str(statement.get('period','N/A')).replace("|", "/")
                 rev = _format_number(statement.get('revenue'))
                 ni = _format_number(statement.get('net_income')) # Correct key
                 eps_diluted = statement.get('earnings_per_share_diluted', 'N/A') # Correct key
                 eps = f"{eps_diluted:.2f}" if isinstance(eps_diluted, (int, float)) else 'N/A'
                 output += f"| {year} | {period:<6} | {rev:<14} | {ni:<14} | {eps:<14} |\n"
            output += "\n"
        else:
             output += "\n### Income Statements\nNot Available\n\n"
    
    # Financial Statements (Balance Sheet)
    balance_sheets_data = data.get("balance_sheets")
    if balance_sheets_data:
        balance_list = balance_sheets_data.get("balance_sheets", [])
        if balance_list:
            output += f"\n### Historical Balance Sheets\n\n"
            output += "| Year | Period | Total Assets   | Total Liab.  | Total Equity   |\n"
            output += "|------|--------|----------------|----------------|----------------|\n"
            for statement in balance_list:
                 year = _get_year_from_date(statement.get('report_period'))
                 period = str(statement.get('period','N/A')).replace("|", "/")
                 assets = _format_number(statement.get('total_assets')) # Correct key
                 liab = _format_number(statement.get('total_liabilities')) # Correct key
                 equity = _format_number(statement.get('shareholders_equity')) # Correct key
                 output += f"| {year} | {period:<6} | {assets:<14} | {liab:<14} | {equity:<14} |\n"
            output += "\n"
        else:
             output += "\n### Balance Sheets\nNot Available\n\n"
    
    # Financial Statements (Cash Flow)
    cash_flow_statements_data = data.get("cash_flow_statements")
    if cash_flow_statements_data:
        cash_flow_list = cash_flow_statements_data.get("cash_flow_statements", [])
        if cash_flow_list:
            output += f"\n### Historical Cash Flow Statements\n\n"
            output += "| Year | Period | Operating CF   | Investing CF   | Free CF        |\n"
            output += "|------|--------|----------------|----------------|----------------|\n"
            for statement in cash_flow_list:
                 year = _get_year_from_date(statement.get('report_period'))
                 period = str(statement.get('period','N/A')).replace("|", "/")
                 ocf = _format_number(statement.get('net_cash_flow_from_operations')) # Correct key
                 icf = _format_number(statement.get('net_cash_flow_from_investing')) # Correct key
                 fcf = _format_number(statement.get('free_cash_flow')) # Correct key
                 output += f"| {year} | {period:<6} | {ocf:<14} | {icf:<14} | {fcf:<14} |\n"
            output += "\n"
        else:
             output += "\n### Cash Flow Statements\nNot Available\n\n"

    # SEC Filings (Keep commented out as per original code)
    # ...
             
    # Insider Trades
    insider_trades_data = data.get("insider_trades")
    if insider_trades_data:
        trades_list = insider_trades_data.get("insider_trades", [])
        # Filter out trades with 0 shares and count actual trades shown
        actual_trades = []
        for trade in trades_list:
            shares_num = trade.get('transaction_shares')
            # Only include if shares_num is not None and not 0
            if shares_num is not None and shares_num != 0:
                actual_trades.append(trade)
                
        if actual_trades: # Check if there are any actual trades to show
            output += "\n### Recent Insider Trades\n\n"
            output += "| Date       | Insider Name      | Title/Rel.     | Type | Shares       | Value ($)   |\n"
            output += "|------------|-------------------|----------------|------|--------------|-------------|\n"
            for trade in actual_trades:
                # Use transaction_date, fallback to filing_date if needed
                trans_date = trade.get('transaction_date')
                filing_date = trade.get('filing_date')
                date = str(trans_date if trans_date else filing_date).replace("|", "/")
                
                name = str(trade.get('name', 'N/A')).replace("|", "/")
                title = str(trade.get('title', 'N/A')).replace("|", "/")
                title_short = title[:11] + "..." if len(title) > 14 else title
                
                shares_num = trade.get('transaction_shares') # Already checked it's non-zero
                type_symbol = "?"
                if shares_num > 0: type_symbol = "A" # Acquisition
                elif shares_num < 0: type_symbol = "D" # Disposition
                
                shares_str = _format_number(shares_num)
                value_str = _format_number(trade.get('transaction_value'))
                
                output += f"| {date:<10} | {name:<17} | {title_short:<14} | {type_symbol:<4} | {shares_str:<12} | {value_str:<11} |\n"
            output += "\n"
        else:
            # Message when the list exists but contains no actual trades
            output += "\n### Recent Insider Trades\nNo recent transactional insider trades found.\n\n"
    # If insider_trades_data itself is missing or the inner list is empty originally
    # else: 
    #    output += "\n### Recent Insider Trades\nNot Available\n\n" 
    # Keep original behaviour: if no data, section is omitted implicitly
             
    # Stock Price
    prices_data = data.get("prices")
    if prices_data:
        prices_list = prices_data.get("prices", [])
        if prices_list:
            output += "\n### Recent Stock Prices (Daily Close)\n\n"
            output += "| Date       | Close Price    |\n"
            output += "|------------|----------------|\n"
            # Show the last 5 prices (or fewer if less data available)
            for price_point in prices_list[:5]: # Iterate through the first 5 (most recent)
                 # Use correct key and helper
                 date = _get_date_from_datetime(price_point.get('time'))
                 close_raw = price_point.get('close')
                 close = f"{close_raw:.2f}" if isinstance(close_raw, (int, float)) else 'N/A'
                 output += f"| {date} | {close:<14} |\n"
            output += "\n"
        else:
            output += "\n### Recent Stock Prices\nNot Available\n\n"
            
    # Press Releases (Using the user-reverted logic)
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
                                # New parameters for stock prices
                                price_interval: Optional[str] = None,
                                price_interval_multiplier: Optional[int] = None,
                                price_start_date: Optional[str] = None,
                                price_end_date: Optional[str] = None,
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
        price_interval: Optional interval for stock prices ('second', 'minute', 'day', 'week', 'month', 'year'). Defaults to 'day'.
        price_interval_multiplier: Optional multiplier for the price interval (e.g., 5 for 5-minute interval). Defaults to 1.
        price_start_date: Optional start date for price data (YYYY-MM-DD). Defaults to 90 days ago.
        price_end_date: Optional end date for price data (YYYY-MM-DD). Defaults to today.
        price_limit: Optional limit for historical stock prices. Defaults to 5000 (API default).
        
    Returns:
        Formatted Markdown string containing detailed financial data tables and lists, or raw JSON if formatting fails.
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
             
        valid_price_intervals = ['second', 'minute', 'day', 'week', 'month', 'year']
        if price_interval and price_interval not in valid_price_intervals:
            return f"Error: Invalid price_interval '{price_interval}'. Must be one of {valid_price_intervals}"
            
        if price_interval_multiplier is not None and price_interval_multiplier < 1:
            return f"Error: Invalid price_interval_multiplier '{price_interval_multiplier}'. Must be >= 1."

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


        #if effective_data_type in ["sec-filings", "all"]:
        #    limit_to_use = filings_limit if filings_limit else 5
        #    result["sec_filings"] = _get_sec_filings(ticker, limit=limit_to_use)
#
        #print("Debug: sec_filings", result["sec_filings"])

        if effective_data_type in ["insider-trades", "all"]:
            limit_to_use = insider_trades_limit if insider_trades_limit else 10
            result["insider_trades"] = _get_insider_trades(ticker, limit=limit_to_use)


        if effective_data_type in ["prices", "all"]:
            # Determine defaults for price parameters if not provided
            interval_to_use = price_interval if price_interval else 'day'
            multiplier_to_use = price_interval_multiplier if price_interval_multiplier is not None else 1
            
            # Default dates: today and 90 days ago
            today = datetime.utcnow().date()
            end_date_to_use = price_end_date if price_end_date else today.strftime('%Y-%m-%d')
            start_date_default = (today - timedelta(days=90)).strftime('%Y-%m-%d')
            start_date_to_use = price_start_date if price_start_date else start_date_default
            
            # Limit is optional in the API call itself, pass it directly
            limit_to_use = price_limit 
            
            result["prices"] = _get_stock_prices(
                ticker=ticker, 
                interval=interval_to_use, 
                interval_multiplier=multiplier_to_use, 
                start_date=start_date_to_use, 
                end_date=end_date_to_use,
                limit=limit_to_use # Pass None if not specified by user, API defaults to 5000
            )

        #if effective_data_type in ["press-releases", "all"]:
        #    result["press_releases"] = _get_press_releases(ticker, limit=1)

        return _format_financial_data(result, ticker)
    except Exception as e:
        print("Debug: error", e)
        return f"Error retrieving financial data for {ticker}: {str(e)}" 