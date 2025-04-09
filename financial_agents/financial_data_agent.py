from pydantic import BaseModel
from typing import List, Optional

from agents import Agent, ModelSettings
# Removed incorrect import: from agents.models.openai import OpenAIChatSettings 

# Use the function tool directly
from financial_agents.financial_data_tool import financial_data_search
# Remove ModelSettings import if no longer needed elsewhere
# from financial_agents.model_settings import ModelSettings 

# Updated prompt to mention ignoring chart data blocks
FINANCIAL_DATA_PROMPT = (
    "You are a meticulous financial data analyst. Your goal is to extract key information and provide **detailed summaries** based **only** on the TEXTUAL content provided by the `financial_data_search` tool. "
    "INPUT: The tool will provide a detailed Markdown output containing tables and lists of financial data (like historical metrics, statements, news, trades, etc.).\n"
    "TASK: \n"
    "1. **Analyze DETAILED Data:** Carefully parse the provided Markdown. Extract specific data points, figures, dates, and list items from the tables and text sections (News, Metrics, Statements, Segments, Filings, Trades, Ownership).\n"
    "2. **Populate Output Fields with DETAILS (NO SUMMARIES):** Fill the output fields below by directly transcribing the relevant detailed information extracted from the input Markdown. DO NOT summarize or synthesize; preserve the original detail, numbers, and structure as much as possible within each field.\n"
    "    *   `financial_summary`: Provide a **detailed** summary of overall financial health, profitability, key statement figures (Revenue, Net Income, EPS from text), and recent performance highlights mentioned in the text.\n"
    "    *   `news_summary`: List the full headlines, dates, and sources for **all** recent news items provided in the input.\n"
    "    *   `insider_trades_summary`: List the details (Date, Name, Relationship, Type, Shares, Value) for **all** reported insider trades from the input table. State if none were reported.\n"
    "    *   `institutional_ownership_summary`: List the details (Name, Shares, Date) for **all** reported top institutional holders from the input table. State if none were reported.\n"
    "    *   `key_metrics`: List the specific values (Year, Period, Market Cap, P/E, Dividend Yield) for **all** historical periods provided in the input metrics table.\n"
    "    *   `growth_analysis`: Extract and state any explicit mentions of growth trends or comparisons found in the input text sections (if any). If none are mentioned, state that.\n"
    "    *   `revenue_segment_analysis`: List the revenue figures for **all** reported segments (Product/Service, Geography, Other) exactly as presented in the input tables/text.\n"
    "    *   `risk_factors`: List **all** risk factors explicitly mentioned in the input text (e.g., from SEC filings section). If none are mentioned, state that.\n"
    "Ensure the ticker symbol passed to the tool is uppercase. Your analysis should strictly reflect the textual information provided by the tool."
)


class FinancialDataAnalysis(BaseModel):
    """Model for the financial data analysis output."""
    
    ticker: str
    """The ticker symbol of the analyzed company."""
    
    company_name: str
    """The full name of the company."""
    
    financial_summary: str # Will contain structured lists/tables of key figures
    """Detailed key figures (Revenue, NI, EPS, Assets, Equity, OCF) for all reported periods, plus basic company info.
       Example: 'Company: X | Industry: Y | Sector: Z\n\nIncome (Annual):\nYear | Revenue | NI | EPS\n...\n\nBalance (Annual):\n...'"""
    
    news_summary: str # List of news items
    """A list of all recent news headlines with dates and sources.
       Example: '* [Date]: Headline (Source)\n* [Date]: Headline (Source)'"""

    insider_trades_summary: str # List or table of trades
    """A list or table detailing all reported insider trades (Date, Name, Type, Shares, Value)."""

    institutional_ownership_summary: Optional[str] = None # List or table of holders
    """Optional list or table detailing all reported top institutional holders (Name, Shares, Date)."""
    
    key_metrics: str # Table or list of metrics
    """Table or list of key financial metrics (Year, Period, Market Cap, P/E, Yield) for all reported periods.
       Example: 'Year | Period | MktCap | PE | Yield\n...'"""
    
    growth_analysis: str # Extracted text or 'Not Mentioned'
    """Explicit growth trend statements extracted from input text, or 'Not Mentioned'."""
    
    revenue_segment_analysis: str # List or tables of segment revenues
    """Detailed breakdown of revenue by all reported segments (Product, Geo, Other) with figures.
       Example: 'Product/Service:\nSegment | Revenue\n...\n\nGeography:\n...'"""
    
    risk_factors: Optional[List[str]] = None
    """Optional list of all risk factors explicitly mentioned in the input text."""


financial_data_agent = Agent(
    name="FinancialDataAgent",
    instructions=FINANCIAL_DATA_PROMPT,
    # Pass the decorated function directly
    tools=[financial_data_search],
    model="gpt-4o",
    output_type=FinancialDataAnalysis,
    # Use the correct ModelSettings class from the SDK
    model_settings=ModelSettings(tool_choice="required"), 
) 