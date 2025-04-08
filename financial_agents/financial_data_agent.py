from pydantic import BaseModel
from typing import List, Optional

from agents import Agent, ModelSettings
# Removed incorrect import: from agents.models.openai import OpenAIChatSettings 

# Use the function tool directly
from financial_agents.financial_data_tool import financial_data_search
# Remove ModelSettings import if no longer needed elsewhere
# from financial_agents.model_settings import ModelSettings 

# Updated prompt to include institutional ownership
FINANCIAL_DATA_PROMPT = (
    "You are a financial data analyst specializing in retrieving and analyzing company financial data. "
    "Given a company name or ticker symbol, use the financial_data_search tool to retrieve key financial "
    "information including recent news, income statements, balance sheets, cash flow statements, key metrics, "
    "segmented revenues, recent SEC filings, recent insider trades, **and top institutional holders**. "
    "Your task is to identify the most relevant ticker symbol based on the query, retrieve the financial data, "
    "and provide a concise analysis of the company's financial health, recent performance, and market sentiment. "
    "Make sure to highlight key metrics, growth trends, and any notable financial developments. "
    "Summarize key information from recent news headlines and consider their potential impact or reflection of market sentiment. "
    "Analyze the segmented revenue data provided by the tool to discuss the company's revenue diversification, main drivers, and potential segment-specific risks. "
    "Analyze the recent insider trading activity provided by the tool. Comment on any significant patterns and their potential implications. "
    "**Briefly comment on the concentration or types of top institutional holders if the data seems significant.** "
    "Consider information from recent SEC filings if relevant. "
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
    
    news_summary: str
    """A brief summary of recent news headlines and their potential sentiment/impact, based *only* on the tool output."""

    insider_trades_summary: str
    """A brief summary and analysis of recent insider trading activity and its potential significance, based *only* on the tool output."""

    institutional_ownership_summary: Optional[str] = None
    """Optional brief commentary on top institutional holders, based *only* on the tool output."""
    
    key_metrics: List[str]
    """List of key financial metrics and their values, extracted *only* from the tool output."""
    
    growth_analysis: str
    """Analysis of the company's growth trends, based *only* on the tool output, including segment growth insights."""
    
    revenue_segment_analysis: str
    """Specific analysis focusing on revenue segments, diversification, drivers, and risks, based *only* on the tool output."""
    
    risk_factors: Optional[List[str]] = None
    """Optional list of identified financial risk factors, based *only* on the tool output, potentially including segment-specific, news-driven, insider-trade, or ownership-related risks."""


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