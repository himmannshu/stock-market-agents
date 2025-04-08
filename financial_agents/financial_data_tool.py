import os
import requests
from typing import Any, Dict, List, Optional

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
    url = f"{BASE_URL}/metrics/historical?ticker={ticker}&period={period}&limit={limit}" 
    return _make_request(url)

def _get_stock_prices(ticker: str, interval: str = "1d", limit: int = 10) -> Dict[str, Any]:
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

def _format_financial_data(data: Dict[str, Any], ticker: str) -> str:
    """Format the retrieved financial data into a readable Markdown summary."""
    summary = f"## Financial Data Summary for {ticker}\n\n"
    
    info = data.get("company_info")
    if info:
        company_data = info.get("company", {}) 
        summary += f"**Company:** {company_data.get('name', ticker)}\n"
        summary += f"**Industry:** {company_data.get('industry', 'N/A')}\n"
        summary += f"**Sector:** {company_data.get('sector', 'N/A')}\n\n"
    
    metrics = data.get("metrics")
    if metrics:
        metrics_list = metrics.get("metrics", [])
        if metrics_list:
             latest_metrics = metrics_list[0] 
             period_label = f"{latest_metrics.get('period','N/A')} {latest_metrics.get('year','N/A')}"
             summary += f"### Latest Key Metrics ({period_label})\n"
             summary += "| Metric         | Value         |\n"
             summary += "|----------------|---------------|\n"
             summary += f"| Market Cap     | {latest_metrics.get('marketCap', 'N/A')} |\n"
             summary += f"| P/E Ratio      | {latest_metrics.get('peRatio', 'N/A')} |\n"
             summary += f"| Dividend Yield | {latest_metrics.get('dividendYield', 'N/A')} |\n\n"
             # Optional: Add more historical periods if needed
             # if len(metrics_list) > 1:
             #     # Add table for previous period(s)
             #     pass 
        else:
            summary += "### Key Metrics\nNot Available\n\n"
            
    income_statements_data = data.get("income_statements")
    if income_statements_data:
        income = income_statements_data.get("income_statements", [])
        if income:
            latest = income[0]
            period_label = f"{latest.get('period', 'N/A')} {latest.get('year', 'N/A')}"
            summary += f"### Latest Income Statement ({period_label})\n"
            summary += "| Item       | Value         |\n"
            summary += "|------------|---------------|\n"
            summary += f"| Revenue    | {latest.get('revenue', 'N/A')} |\n"
            summary += f"| Net Income | {latest.get('netIncome', 'N/A')} |\n"
            summary += f"| EPS        | {latest.get('eps', 'N/A')} |\n\n"
        else:
             summary += "### Latest Income Statement\nNot Available\n\n"
    
    balance_sheets_data = data.get("balance_sheets")
    if balance_sheets_data:
        balance = balance_sheets_data.get("balance_sheets", [])
        if balance:
            latest = balance[0]
            period_label = f"{latest.get('period', 'N/A')} {latest.get('year', 'N/A')}"
            summary += f"### Latest Balance Sheet ({period_label})\n"
            summary += "| Item             | Value         |\n"
            summary += "|------------------|---------------|\n"
            summary += f"| Total Assets     | {latest.get('totalAssets', 'N/A')} |\n"
            summary += f"| Total Liabilities| {latest.get('totalLiabilities', 'N/A')} |\n"
            summary += f"| Total Equity     | {latest.get('totalEquity', 'N/A')} |\n\n"
        else:
             summary += "### Latest Balance Sheet\nNot Available\n\n"
    
    cash_flow_statements_data = data.get("cash_flow_statements")
    if cash_flow_statements_data:
        cash_flow = cash_flow_statements_data.get("cash_flow_statements", [])
        if cash_flow:
            latest = cash_flow[0]
            period_label = f"{latest.get('period', 'N/A')} {latest.get('year', 'N/A')}"
            summary += f"### Latest Cash Flow Statement ({period_label})\n"
            summary += "| Item                  | Value         |\n"
            summary += "|-----------------------|---------------|\n"
            summary += f"| Operating Cash Flow   | {latest.get('operatingCashFlow', 'N/A')} |\n"
            summary += f"| Investing Cash Flow   | {latest.get('investingCashFlow', 'N/A')} |\n"
            summary += f"| Free Cash Flow        | {latest.get('freeCashFlow', 'N/A')} |\n\n"
        else:
             summary += "### Latest Cash Flow Statement\nNot Available\n\n"
             
    segmented_revenues_data = data.get("segmented_revenues")
    if segmented_revenues_data:
        segments_list = segmented_revenues_data.get("segmented_revenues", [])
        if segments_list:
            latest_segment_report = segments_list[0]
            period_label = f"{latest_segment_report.get('period', 'N/A')} {latest_segment_report.get('report_period', 'N/A')}"
            summary += f"### Segmented Revenues ({period_label})\n"
            
            product_segments = {}
            geo_segments = {}
            other_segments = {}

            for item in latest_segment_report.get("items", []):
                amount = item.get('amount', 0)
                # Assuming one segment label per item for simplicity in this summary
                segment_info = item.get("segments", [{}])[0]
                label = segment_info.get("label", "Unknown Segment")
                seg_type = segment_info.get("type", "Unknown Type")
                
                # Group by common segment types
                if "Product" in seg_type or "Service" in seg_type:
                    product_segments[label] = amount
                elif "Geographic" in seg_type or "Region" in seg_type or "Countr" in seg_type or "Segment" in seg_type: # Heuristic for geo
                    geo_segments[label] = amount
                else:
                    other_segments[label] = amount
            
            if product_segments:
                summary += "**By Product/Service:**\n"
                summary += "| Segment        | Revenue       |\n"
                summary += "|----------------|---------------|\n"
                for label, amount in product_segments.items():
                    summary += f"| {label:<14} | {amount:<13} |\n" 
                summary += "\n"
            
            if geo_segments:
                summary += "**By Geography/Segment:**\n"
                summary += "| Segment        | Revenue       |\n"
                summary += "|----------------|---------------|\n"
                for label, amount in geo_segments.items():
                     summary += f"| {label:<14} | {amount:<13} |\n"
                summary += "\n"
            
            if other_segments:
                summary += "**By Other Segments:**\n"
                summary += "| Segment        | Revenue       |\n"
                summary += "|----------------|---------------|\n"
                for label, amount in other_segments.items():
                     summary += f"| {label:<14} | {amount:<13} |\n"
                summary += "\n"

        else:
            summary += "### Segmented Revenues\nNot Available\n\n"
             
    prices_data = data.get("prices")
    if prices_data:
        prices = prices_data.get("prices", [])
        if prices:
            latest = prices[0]
            summary += "### Latest Stock Price\n"
            summary += f"**Date:** {latest.get('date', 'N/A')}\n"
            summary += f"**Close:** {latest.get('close', 'N/A')}\n\n"
        else:
            summary += "### Latest Stock Price\nNot Available\n\n"
            
    press_releases_data = data.get("press_releases")
    if press_releases_data:
        releases = press_releases_data.get("press_releases", [])
        if releases:
            latest = releases[0]
            summary += "### Latest Earnings Press Release\n"
            summary += f"**Title:** {latest.get('title', 'N/A')}\n"
            summary += f"**Date:** {latest.get('date', 'N/A')}\n"
            # summary += f"**URL:** [{latest.get('title', 'Link')}]({latest.get('url', '#')})\n"
        else:
            summary += "### Latest Earnings Press Release\nNot Available\n"
            
    return summary.strip()


@function_tool
async def financial_data_search(ticker: str, 
                                data_type: str, 
                                metrics_period: Optional[str] = None, 
                                metrics_limit: Optional[int] = None,
                                segmented_period: Optional[str] = None,
                                segmented_limit: Optional[int] = None) -> str:
    """
    Search for financial data about a company using Financial Datasets API.
    Retrieves company info, historical key metrics, latest annual statements (income, balance, cash flow), 
    segmented revenues, recent price, and latest earnings press release.
    
    Args:
        ticker: The stock ticker symbol (e.g., AAPL, MSFT, GOOGL). Should be uppercase.
        data_type: Type of data to retrieve (must be one of 'income', 'balance', 'cash-flow', 'metrics', 'prices', 'info', 'press-releases', 'segmented-revenues', or 'all').
        metrics_period: Optional period for historical metrics ('annual' or 'quarterly'). Defaults to 'annual' if metrics are requested.
        metrics_limit: Optional limit for number of historical metrics periods. Defaults to 3 if metrics are requested.
        segmented_period: Optional period for segmented revenues ('annual' or 'quarterly'). Defaults to 'annual' if segmented revenues are requested.
        segmented_limit: Optional limit for number of segmented revenue periods. Defaults to 1 if segmented revenues are requested.
        
    Returns:
        Formatted summary of the financial data or an error message.
    """
    try:
        result = {}
        ticker = ticker.upper() 
        
        valid_data_types = ["income", "balance", "cash-flow", "metrics", "prices", "info", "press-releases", "segmented-revenues", "all"]
        if data_type not in valid_data_types:
            return f"Error: Invalid data_type '{data_type}'. Must be one of {valid_data_types}"
            
        valid_periods = ["annual", "quarterly"]
        if metrics_period and metrics_period not in valid_periods:
             return f"Error: Invalid metrics_period '{metrics_period}'. Must be one of {valid_periods}"
        if segmented_period and segmented_period not in valid_periods:
             return f"Error: Invalid segmented_period '{segmented_period}'. Must be one of {valid_periods}"

        effective_data_type = data_type if data_type else "all"

        if effective_data_type in ["info", "all"]:
            result["company_info"] = _get_company_info(ticker)
            
        if effective_data_type in ["metrics", "all"]:
            period_to_use = metrics_period if metrics_period else "annual"
            limit_to_use = metrics_limit if metrics_limit else 3
            result["metrics"] = _get_company_metrics(ticker, period=period_to_use, limit=limit_to_use)
            
        if effective_data_type in ["income", "all"]:
            result["income_statements"] = _get_financial_statements(ticker, "income-statements", "annual", 1)
            
        if effective_data_type in ["balance", "all"]:
            result["balance_sheets"] = _get_financial_statements(ticker, "balance-sheets", "annual", 1)
            
        if effective_data_type in ["cash-flow", "all"]:
            result["cash_flow_statements"] = _get_financial_statements(ticker, "cash-flow-statements", "annual", 1)

        if effective_data_type in ["segmented-revenues", "all"]:
            period_to_use = segmented_period if segmented_period else "annual"
            limit_to_use = segmented_limit if segmented_limit else 1
            result["segmented_revenues"] = _get_segmented_revenues(ticker, period=period_to_use, limit=limit_to_use)
            
        if effective_data_type in ["prices", "all"]:
            result["prices"] = _get_stock_prices(ticker, limit=1)
            
        if effective_data_type in ["press-releases", "all"]:
             result["press_releases"] = _get_press_releases(ticker, limit=1)
        
        return _format_financial_data(result, ticker)
        
    except Exception as e:
        return f"Error retrieving financial data for {ticker}: {str(e)}" 