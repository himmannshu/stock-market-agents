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
    "You are a financial data analyst specializing in retrieving and analyzing company financial data. "
    "Given a company name or ticker symbol, use the financial_data_search tool to retrieve key financial information. " 
    "The tool output will contain both textual summaries and structured data blocks (e.g., CSV in ```) intended for charts. **Focus your analysis ONLY on the textual summary parts.** "
    "Retrieve data including recent news, financial statements, metrics, segmented revenues, SEC filings, insider trades, and institutional holders. "
    "Your task is to identify the most relevant ticker symbol, retrieve the data using the tool, and provide a concise analysis of the company's financial health, performance, and market sentiment **based on the textual summaries provided by the tool.** "
    "Highlight key metrics, growth trends, and notable financial developments. "
    "Summarize news and sentiment. Analyze revenue segments. Analyze insider trades. Briefly comment on ownership. "
    "Consider SEC filings. **Do NOT attempt to analyze or interpret the raw data within the ```csv or ```json blocks.** "
    "After analyzing the text, locate the section in the tool's raw output between `<!-- CHART DATA START -->` and `<!-- CHART DATA END -->`. Extract this entire section verbatim, including the start/end markers and all content within. Place this extracted block into the `raw_chart_data` output field. "
    "Ensure the ticker symbol passed to the tool is uppercase."
)


class FinancialDataAnalysis(BaseModel):
    """Model for the financial data analysis output."""
    
    ticker: str
    """The ticker symbol of the analyzed company."""
    
    company_name: str
    """The full name of the company."""
    
    financial_summary: str
    """A comprehensive summary based *only* on the TEXTUAL parts of the tool output. Includes financial performance, segments, etc."""
    
    news_summary: str
    """A brief summary of recent news headlines based *only* on the TEXTUAL parts of the tool output."""

    insider_trades_summary: str
    """A brief summary and analysis of recent insider trading activity based *only* on the TEXTUAL parts of the tool output."""

    institutional_ownership_summary: Optional[str] = None
    """Optional brief commentary on top institutional holders based *only* on the TEXTUAL parts of the tool output."""
    
    key_metrics: List[str] # This might become less useful if metrics summary is in financial_summary
    """List of key financial metrics values extracted *only* from the TEXTUAL summary in the tool output."""
    
    growth_analysis: str
    """Analysis of growth trends based *only* on the TEXTUAL parts of the tool output."""
    
    revenue_segment_analysis: str
    """Analysis of revenue segments based *only* on the TEXTUAL parts of the tool output."""
    
    risk_factors: Optional[List[str]] = None
    """Optional list of identified financial risk factors based *only* on the TEXTUAL parts of the tool output."""

    raw_chart_data: Optional[str] = None
    """The verbatim chart data block (including markers) extracted from the tool output, intended for frontend visualization."""


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