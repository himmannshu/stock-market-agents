from pydantic import BaseModel
from typing import List, Optional

from agents import Agent, ModelSettings

from financial_agents.financial_data_tool import financial_data_search


# Updated prompt to directly pass markdown sections
FINANCIAL_DATA_PROMPT = (
    "You are a meticulous financial data analyst. Your goal is to extract key information and structure it based **only** on the TEXTUAL content provided by the `financial_data_search` tool. "
    "INPUT: The tool will provide a detailed Markdown output containing a header (`## Financial Data Details for TICKER`), company info, and various sections (e.g., `### Recent News`, `### Top Institutional Holders`, `### Historical Key Metrics`, etc.) containing text, lists, and tables.\n"
    "TASK: \n"
    "1. **Extract Key Info:** Identify the Ticker Symbol and Company Name from the input header or company info section.\n"
    "2. **Extract Sections as Markdown:** Copy the complete Markdown content for each relevant section (including the `###` header and all subsequent text/tables until the next `###` header or end of input) directly into the corresponding output field below. \n"
    "3. **Generate Text Summaries Where Specified:** For fields like `financial_summary` and `growth_analysis`, provide purely textual summaries based on the overall input.\n"
    "OUTPUT FIELDS:\n"
    "    *   `ticker`: Extracted Ticker Symbol.\n"
    "    *   `company_name`: Extracted Company Name.\n"
    "    *   `company_info_markdown`: The Markdown block containing company info (Industry, Sector)."""
    "    *   `news_markdown`: The Markdown block for the 'Recent News' section.\n"
    "    *   `institutional_ownership_markdown`: The Markdown block for the 'Top Institutional Holders' section (if present).\n"
    "    *   `key_metrics_markdown`: The Markdown block for the 'Historical Key Metrics' section (if present).\n"
    "    *   `segmented_revenues_markdown`: The Markdown block for the 'Segmented Revenues' section (if present).\n"
    "    *   `income_statements_markdown`: The Markdown block for the 'Historical Income Statements' section (if present).\n"
    "    *   `balance_sheets_markdown`: The Markdown block for the 'Historical Balance Sheets' section (if present).\n"
    "    *   `cash_flows_markdown`: The Markdown block for the 'Historical Cash Flow Statements' section (if present).\n"
    "    *   `insider_trades_markdown`: The Markdown block for the 'Recent Insider Trades' section (if present).\n"
    "    *   `stock_prices_markdown`: The Markdown block for the 'Recent Stock Prices' section (if present).\n"
    "    *   `press_releases_markdown`: The Markdown block for the 'Latest Earnings Press Release' section (if present).\n"
    "    *   `financial_summary`: A brief **textual** summary (2-3 sentences) of the company's overall financial health and recent performance highlights mentioned in the text. DO NOT include tables here.\n"
    "    *   `growth_analysis`: Extract and state any explicit textual mentions of growth trends or comparisons found in the input text sections (if any). If none are mentioned, state 'No specific growth trends mentioned in the provided text.'. DO NOT include tables here.\n"
    "    *   `risk_factors`: List **all** risk factors explicitly mentioned in the input text (e.g., from an SEC filings section if it were present). If none are mentioned, state 'No specific risk factors mentioned in the provided text.'.\n"
    "Ensure the output fields contain the full, raw Markdown for the sections requested, including headers and table formatting."
)


class FinancialDataAnalysis(BaseModel):
    """Model for the structured financial data extracted from markdown."""
    
    ticker: str
    """The ticker symbol of the analyzed company."""
    
    company_name: str
    """The full name of the company."""

    # Fields to hold raw markdown sections
    company_info_markdown: Optional[str] = None
    """Markdown block for company info (Industry, Sector)."""
    news_markdown: Optional[str] = None
    """Markdown block for the 'Recent News' section."""
    institutional_ownership_markdown: Optional[str] = None
    """Markdown block for the 'Top Institutional Holders' section."""
    key_metrics_markdown: Optional[str] = None
    """Markdown block for the 'Historical Key Metrics' section."""
    segmented_revenues_markdown: Optional[str] = None
    """Markdown block for the 'Segmented Revenues' section."""
    income_statements_markdown: Optional[str] = None
    """Markdown block for the 'Historical Income Statements' section."""
    balance_sheets_markdown: Optional[str] = None
    """Markdown block for the 'Historical Balance Sheets' section."""
    cash_flows_markdown: Optional[str] = None
    """Markdown block for the 'Historical Cash Flow Statements' section."""
    insider_trades_markdown: Optional[str] = None
    """Markdown block for the 'Recent Insider Trades' section."""
    stock_prices_markdown: Optional[str] = None
    """Markdown block for the 'Recent Stock Prices' section."""
    press_releases_markdown: Optional[str] = None
    """Markdown block for the 'Latest Earnings Press Release' section."""
    
    # Textual summary fields
    financial_summary: str 
    """Brief textual summary of overall financial health and recent performance."""
    growth_analysis: str 
    """Explicit growth trend statements extracted from input text, or a note if none found."""
    risk_factors: Optional[str] = None # Changed to string for simplicity
    """Explicit risk factors mentioned in the input text, or a note if none found."""


financial_data_agent = Agent(
    name="FinancialDataAgent",
    instructions=FINANCIAL_DATA_PROMPT,
    tools=[financial_data_search],
    model="gpt-4o",
    output_type=FinancialDataAnalysis,
    model_settings=ModelSettings(tool_choice="required"), 
) 