from pydantic import BaseModel
from typing import List, Optional

from agents import Agent, ModelSettings
# Removed incorrect import: from agents.models.openai import OpenAIChatSettings 

# Use the function tool directly
from financial_agents.financial_data_tool import financial_data_search
# Remove ModelSettings import if no longer needed elsewhere
# from financial_agents.model_settings import ModelSettings 

# Financial data agent fetches and analyzes company financial data using the financial_data_search tool
FINANCIAL_DATA_PROMPT = (
    "You are a financial data analyst specializing in retrieving and analyzing company financial data. "
    "Given a company name or ticker symbol, use the financial_data_search tool to retrieve key financial "
    "information including income statements, balance sheets, cash flow statements, key metrics, and **segmented revenues**. "
    "Your task is to identify the most relevant ticker symbol based on the query, retrieve the financial data, "
    "and provide a concise analysis of the company's financial health and recent performance. "
    "Make sure to highlight key metrics, growth trends, and any notable financial developments. "
    "**Crucially, analyze the segmented revenue data provided by the tool to discuss the company's revenue diversification, main drivers, and potential segment-specific risks.** "
    "Ensure the ticker symbol passed to the tool is uppercase."
)


class FinancialDataAnalysis(BaseModel):
    """Model for the financial data analysis output."""
    
    ticker: str
    """The ticker symbol of the analyzed company."""
    
    company_name: str
    """The full name of the company."""
    
    financial_summary: str
    """A comprehensive summary of the company's financial data and performance, based *only* on the tool output. Must include analysis of segmented revenues."""
    
    key_metrics: List[str]
    """List of key financial metrics and their values, extracted *only* from the tool output."""
    
    growth_analysis: str
    """Analysis of the company's growth trends, based *only* on the tool output, including segment growth insights."""
    
    revenue_segment_analysis: str
    """Specific analysis focusing on revenue segments, diversification, drivers, and risks, based *only* on the tool output."""
    
    risk_factors: Optional[List[str]] = None
    """Optional list of identified financial risk factors, based *only* on the tool output, potentially including segment-specific risks."""


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