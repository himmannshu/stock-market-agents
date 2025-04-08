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
    "INPUT: The tool will provide Markdown output containing textual summaries and potentially ```csv/json``` blocks for charts.\n"
    "TASK: \n"
    "1. **Analyze Text ONLY:** Carefully read all the textual summaries provided by the tool (sections like News, Metrics, Statements, Segments, Filings, Trades, Ownership). Ignore data inside ```csv/json``` blocks.\n"
    "2. **Extract Chart Data Block:** Locate the section between `<!-- CHART DATA START -->` and `<!-- CHART DATA END -->`. Extract this entire block verbatim into the `raw_chart_data` field.\n"
    "3. **Populate Output Fields with DETAIL:** Fill the output fields below based *only* on your analysis of the textual summaries. Be specific, include numbers, dates, key figures, and trends mentioned in the text.\n"
    "    *   `financial_summary`: Provide a **detailed** summary of overall financial health, profitability, key statement figures (Revenue, Net Income, EPS from text), and recent performance highlights mentioned in the text.\n"
    "    *   `news_summary`: Summarize the **key points** from recent news headlines provided in the text, noting any sentiment indicators if mentioned.\n"
    "    *   `insider_trades_summary`: Summarize **specific details** of recent insider trades (who, what type, volume/value if mentioned in text). State if no significant trades were reported in the text.\n"
    "    *   `institutional_ownership_summary`: Summarize **key institutional holders** or trends mentioned in the textual summary. State if not available in the text.\n"
    "    *   `key_metrics`: List **specific values** for key metrics (like P/E, Market Cap, Yield) IF they are explicitly stated in the textual summary sections.\n"
    "    *   `growth_analysis`: Analyze growth trends based on **specific numbers or percentages** mentioned in the textual summaries (e.g., revenue growth %, EPS growth %).\n"
    "    *   `revenue_segment_analysis`: Provide a **detailed breakdown** of revenue by segment based on the textual description, including specific segment names and revenue figures/percentages if mentioned.\n"
    "    *   `risk_factors`: List **specific risk factors** identified in the textual summaries or filings section.\n"
    "Ensure the ticker symbol passed to the tool is uppercase. Your analysis should strictly reflect the textual information provided by the tool."
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