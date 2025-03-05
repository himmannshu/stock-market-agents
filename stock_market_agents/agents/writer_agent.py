"""Writer agent for generating markdown reports."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..models.research import ResearchResults

logger = logging.getLogger(__name__)

class WriterAgent:
    """Agent for writing markdown reports."""
    
    def __init__(self):
        """Initialize the writer agent."""
        pass
        
    async def write_report(self, question: str, results: List[ResearchResults], analysis: Dict[str, Any], output_path: str) -> None:
        """Write a markdown report based on research results.
        
        Args:
            question: Original research question
            results: List of research results
            analysis: Analysis results from LLM
            output_path: Path to save the report
        """
        try:
            logger.info("Generating markdown report")
            
            # Start with report header
            report = f"""# Financial Analysis Report

Analysis Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Companies Analyzed: {", ".join(r.company_profile.ticker for r in results if r.company_profile)}
Confidence Score: {analysis.get("confidence", 0)*100:.2f}%
Data Sources: Alpha Vantage API, SEC Filings

## Executive Summary

Key Insights:
{chr(10).join(f"- {insight}" for insight in analysis.get("insights", ["Analysis failed"]))}

Comparative Analysis:
{chr(10).join(f"- {comp}" for comp in analysis.get("comparisons", []))}

Limitations:
{chr(10).join(f"- {limit}" for limit in analysis.get("limitations", ["Error processing results"]))}

Recommendations:
{chr(10).join(f"- {rec}" for rec in analysis.get("recommendations", []))}

## Company Analysis

"""
            
            # Add section for each company
            for result in results:
                if not result.company_profile:
                    continue
                    
                report += f"""
### {result.company_profile.name} ({result.company_profile.ticker})

Financial Health
---------------
| Metric | Value |
|---|---|
| Gross Margin | {result.company_profile.gross_margin:.2f}% |
| Operating Margin | {result.company_profile.operating_margin:.2f}% |
| Profit Margin | {result.company_profile.profit_margin:.2f}% |

Growth Analysis
--------------
Revenue Growth (TTM): {result.company_profile.revenue_growth:.2f}%

Quarterly Revenue Growth:
| Quarter | Revenue |
|---|---|
"""
                
                # Add quarterly revenue data
                if result.financial_metrics and result.financial_metrics.total_revenue:
                    for i, revenue in enumerate(result.financial_metrics.total_revenue[:4]):
                        report += f"| Q{i+1} | ${revenue:,.2f} |\n"
                
                # Add stock performance section
                if result.stock_data:
                    max_price = max(result.stock_data.historical_prices[:30]) * 1.1 if result.stock_data.historical_prices else 300
                    price_data = str(result.stock_data.historical_prices[:30]).strip('[]') if result.stock_data.historical_prices else ''
                    ma50_data = str([result.stock_data.ma_50] * 30).strip('[]')
                    ma200_data = str([result.stock_data.ma_200] * 30).strip('[]')
                    
                    report += f"""
Stock Performance
----------------
Current Price: ${result.stock_data.current_price:.2f}
52-Week High: ${result.stock_data.high_52week:.2f}
52-Week Low: ${result.stock_data.low_52week:.2f}
RSI: {result.stock_data.rsi:.2f}
Beta: {result.stock_data.beta:.2f}
Volatility: {result.stock_data.volatility:.2f}%

```mermaid
xychart-beta
title "{result.company_profile.ticker} Stock Price"
x-axis ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30"]
y-axis "Price ($)" 0 --> {max_price}
line ["Price", "MA50", "MA200"]
{price_data}
{ma50_data}
{ma200_data}
```
"""
            
                # Add news section
                if result.news_data:
                    report += "\n## Recent News & Analysis\n\n"
                    
                    # Add news articles
                    report += "### Top News Articles\n\n"
                    for article in result.news_data.articles:
                        if article.get("type") == "analysis":
                            continue
                        
                        report += f"**{article['title']}**\n"
                        report += f"- Published: {article['published_date']}\n"
                        report += f"- Summary: {article['summary']}\n"
                        report += f"- Sentiment: {article['sentiment']}\n"
                        report += f"- [Read more]({article['url']})\n\n"
                    
                    # Add analysis if available
                    analysis = next((a for a in result.news_data.articles if a.get("type") == "analysis"), None)
                    if analysis:
                        report += "### News Analysis\n\n"
                        report += f"{analysis['content']}\n\n"
            
            # Write report to file
            with open(output_path, 'w') as f:
                f.write(report)
                
            logger.info(f"Report saved to: {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to generate report: {str(e)}", exc_info=True)
            raise
