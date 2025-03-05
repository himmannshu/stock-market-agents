"""Writer agent for generating markdown reports."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import io
import base64
import matplotlib.pyplot as plt
import numpy as np

from ..models.research import ResearchResults

logger = logging.getLogger(__name__)

class WriterAgent:
    """Agent for writing markdown reports."""
    
    def __init__(self):
        """Initialize the writer agent."""
        pass
        
    def _generate_stock_chart(self, ticker: str, prices: List[float], ma50: float, ma200: float) -> str:
        """Generate a base64-encoded image of a stock chart.
        
        Args:
            ticker: Stock ticker symbol
            prices: List of historical prices
            ma50: 50-day moving average
            ma200: 200-day moving average
            
        Returns:
            Base64-encoded PNG image
        """
        try:
            # Create a new figure
            plt.figure(figsize=(10, 6))
            
            # Plot data
            days = list(range(1, len(prices) + 1))
            plt.plot(days, prices, label='Price', linewidth=2)
            plt.axhline(y=ma50, color='r', linestyle='-', label='MA50')
            plt.axhline(y=ma200, color='g', linestyle='-', label='MA200')
            
            # Add labels and title
            plt.title(f"{ticker} Stock Price")
            plt.xlabel("Day")
            plt.ylabel("Price ($)")
            plt.grid(True, alpha=0.3)
            plt.legend()
            
            # Save to a bytes buffer
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=100)
            plt.close()
            
            # Convert to base64
            buffer.seek(0)
            img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # Return as markdown image
            return f"![{ticker} Stock Chart](data:image/png;base64,{img_str})"
            
        except Exception as e:
            logger.error(f"Failed to generate chart: {str(e)}", exc_info=True)
            return f"*Chart generation failed: {str(e)}*"
    
    def _generate_revenue_chart(self, ticker: str, periods: List[str], revenues: List[float]) -> str:
        """Generate a base64-encoded image of a revenue chart.
        
        Args:
            ticker: Stock ticker symbol
            periods: List of period labels
            revenues: List of revenue values
            
        Returns:
            Base64-encoded PNG image
        """
        try:
            # Create a new figure
            plt.figure(figsize=(10, 6))
            
            # Plot data
            x = np.arange(len(periods))
            plt.bar(x, revenues, width=0.6, color='blue', alpha=0.7)
            
            # Format the revenue values on top of bars
            for i, v in enumerate(revenues):
                plt.text(i, v + max(revenues)*0.01, 
                        f"${v/1000000:.1f}M" if v < 1000000000 else f"${v/1000000000:.2f}B", 
                        ha='center', fontweight='bold')
            
            # Add labels and title
            plt.title(f"{ticker} Quarterly Revenue")
            plt.ylabel("Revenue ($)")
            plt.xticks(x, periods)
            plt.grid(True, axis='y', alpha=0.3)
            
            # Save to a bytes buffer
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=100)
            plt.close()
            
            # Convert to base64
            buffer.seek(0)
            img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # Return as markdown image
            return f"![{ticker} Revenue Chart](data:image/png;base64,{img_str})"
            
        except Exception as e:
            logger.error(f"Failed to generate revenue chart: {str(e)}", exc_info=True)
            return f"*Revenue chart generation failed: {str(e)}*"
        
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
            
            # Track companies we've already processed to avoid duplication
            processed_tickers = set()
            
            # Filter out duplicate results or results without company profiles
            unique_results = []
            for result in results:
                if result.company_profile and result.company_profile.ticker and result.company_profile.ticker not in processed_tickers:
                    processed_tickers.add(result.company_profile.ticker)
                    unique_results.append(result)
            
            # Get company names for the report header
            company_names = []
            for r in unique_results:
                if r.company_profile and r.company_profile.name:
                    company_names.append(r.company_profile.name)
                elif r.company_profile and hasattr(r.company_profile, 'ticker'):
                    company_names.append(r.company_profile.ticker)  # Use ticker if name not available
            
            # If no company names found, use the question to extract potential company names
            if not company_names and len(results) > 0:
                for result in results:
                    if result.company_profile and hasattr(result.company_profile, 'ticker'):
                        company_names.append(result.company_profile.ticker)
            
            # Start with report header
            report = f"""# Financial Analysis Report

Analysis Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Companies Analyzed: {", ".join(company_names) if company_names else "N/A"}
Question: {question}
Confidence Score: {analysis.get("confidence", 0)*100:.2f}%
Data Sources: Alpha Vantage API, SEC Filings

## Executive Summary

Key Insights:
{chr(10).join(f"- {insight}" for insight in analysis.get("insights", ["Analysis failed to generate specific insights"]) if insight)}

Comparative Analysis:
{chr(10).join(f"- {comp}" for comp in analysis.get("comparisons", []) if comp)}

Limitations:
{chr(10).join(f"- {limit}" for limit in analysis.get("limitations", ["Error processing results"]) if limit)}

Recommendations:
{chr(10).join(f"- {rec}" for rec in analysis.get("recommendations", []) if rec)}

## Company Analysis

"""
            
            # Add section for each unique company or just one section if no companies found
            if not unique_results and len(results) > 0:
                # Create a generic section with available data
                report += self._generate_generic_data_section(question, results, analysis)
            else:
                for result in unique_results:
                    # Skip if no company profile
                    if not result.company_profile:
                        continue
                        
                    # Generate company section with proper null handling
                    report += self._generate_company_section(result)
                    
            # Add research data section to show what was actually found
            report += "\n## Research Data Summary\n\n"
            
            research_summary = []
            # Add data availability information
            for result in results:
                ticker = result.company_profile.ticker if result.company_profile and hasattr(result.company_profile, 'ticker') else "Unknown"
                
                # Check what data was successfully retrieved
                data_points = []
                
                if result.company_profile:
                    profile_data = []
                    if result.company_profile.name:
                        profile_data.append("company name")
                    if result.company_profile.sector:
                        profile_data.append("sector")
                    if result.company_profile.market_cap > 0:
                        profile_data.append("market cap")
                    if result.company_profile.pe_ratio > 0:
                        profile_data.append("P/E ratio")
                    if result.company_profile.profit_margin != 0:
                        profile_data.append("profit margins")
                    if profile_data:
                        data_points.append(f"Profile data ({', '.join(profile_data)})")
                
                if result.financial_metrics:
                    metrics_data = []
                    if result.financial_metrics.total_revenue:
                        metrics_data.append("revenue")
                    if result.financial_metrics.net_income:
                        metrics_data.append("net income")
                    if result.financial_metrics.eps:
                        metrics_data.append("EPS")
                    if metrics_data:
                        data_points.append(f"Financial metrics ({', '.join(metrics_data)})")
                
                if result.balance_sheet:
                    bs_data = []
                    if result.balance_sheet.total_assets:
                        bs_data.append("assets")
                    if result.balance_sheet.total_liabilities:
                        bs_data.append("liabilities")
                    if result.balance_sheet.cash_and_equivalents:
                        bs_data.append("cash")
                    if bs_data:
                        data_points.append(f"Balance sheet ({', '.join(bs_data)})")
                        
                if result.stock_data:
                    stock_data = []
                    if result.stock_data.current_price > 0:
                        stock_data.append("price")
                    if result.stock_data.volume > 0:
                        stock_data.append("volume")
                    if result.stock_data.rsi > 0:
                        stock_data.append("RSI")
                    if result.stock_data.ma_50 > 0:
                        stock_data.append("MA50")
                    if result.stock_data.ma_200 > 0:
                        stock_data.append("MA200")
                    if stock_data:
                        data_points.append(f"Stock data ({', '.join(stock_data)})")
                
                if result.news_data:
                    news_count = len(result.news_data.articles) if result.news_data.articles else 0
                    if news_count > 0:
                        data_points.append(f"News articles ({news_count})")
                
                if data_points:
                    research_summary.append(f"- **{ticker}**: {', '.join(data_points)}")
                else:
                    research_summary.append(f"- **{ticker}**: No data retrieved")
            
            report += "\n".join(research_summary)
            
            # Add the error section
            if any(r.error for r in results):
                report += "\n\n## Errors and Limitations\n\n"
                for r in results:
                    if r.error:
                        ticker = r.company_profile.ticker if r.company_profile and hasattr(r.company_profile, 'ticker') else "Unknown"
                        report += f"- **{ticker}**: {r.error}\n"
                
            # Save the report
            with open(output_path, "w") as f:
                f.write(report)
                
            logger.info(f"Report saved to {output_path}")
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}", exc_info=True)
            
            # Create a basic error report
            error_report = """# Financial Analysis Error Report

An error occurred during the generation of the financial analysis report.
            
## Error Details

"""
            error_report += f"Error: {str(e)}\n\n"
            error_report += f"Question: {question}\n\n"
            
            # Add whatever data we have
            for i, result in enumerate(results):
                error_report += f"### Data Set {i+1}\n"
                
                if result.company_profile and hasattr(result.company_profile, 'ticker'):
                    error_report += f"Ticker: {result.company_profile.ticker}\n\n"
                
                if result.company_profile:
                    error_report += "Company profile data was retrieved.\n\n"
                
                if result.financial_metrics:
                    error_report += "Financial data was retrieved.\n\n"
                
                if result.stock_data:
                    error_report += "Stock price data was retrieved.\n\n"
                
                if result.news_data:
                    error_report += "News data was retrieved.\n\n"
                
                if result.error:
                    error_report += f"Original error: {result.error}\n\n"
            
            # Save the error report
            with open(output_path, "w") as f:
                f.write(error_report)
                
            # Re-raise the exception
            raise
    
    def _generate_generic_data_section(self, question: str, results: List[ResearchResults], analysis: Dict[str, Any]) -> str:
        """Generate a generic data section when complete company profiles aren't available.
        
        Args:
            question: Original research question
            results: List of research results
            analysis: Analysis results from LLM
            
        Returns:
            Markdown section with available data
        """
        section = f"### Analysis Results for: {question}\n\n"
        
        # Extract whatever data we have from results
        all_tickers = []
        for r in results:
            if r.company_profile and hasattr(r.company_profile, 'ticker'):
                all_tickers.append(r.company_profile.ticker)
        
        if all_tickers:
            section += f"Tickers analyzed: {', '.join(all_tickers)}\n\n"
            
        # Add financial metrics if available
        financial_metrics = []
        for result in results:
            if result.company_profile:
                ticker = result.company_profile.ticker if hasattr(result.company_profile, 'ticker') else "Unknown"
                if result.company_profile.revenue_growth != 0:
                    financial_metrics.append(f"Revenue Growth ({ticker}): {result.company_profile.revenue_growth:.2f}%")
                if result.company_profile.profit_margin != 0:
                    financial_metrics.append(f"Profit Margin ({ticker}): {result.company_profile.profit_margin:.2f}%")
                if result.company_profile.operating_margin != 0:
                    financial_metrics.append(f"Operating Margin ({ticker}): {result.company_profile.operating_margin:.2f}%")
                if result.company_profile.gross_margin != 0:
                    financial_metrics.append(f"Gross Margin ({ticker}): {result.company_profile.gross_margin:.2f}%")
            
        if financial_metrics:
            section += "#### Financial Metrics\n\n"
            section += "\n".join(f"- {metric}" for metric in financial_metrics)
            section += "\n\n"
        else:
            section += "No specific financial metrics were found in the research data.\n\n"
            
        # Add news summary if available
        all_news = []
        for result in results:
            if result.news_data and result.news_data.articles:
                for news_item in result.news_data.articles:
                    all_news.append(news_item)
                    
        if all_news:
            section += "#### Recent News\n\n"
            for i, news in enumerate(all_news[:5]):  # Show at most 5 news items
                title = news.get('title', 'Untitled')
                date = news.get('date', '')
                summary = news.get('summary', '')
                
                section += f"- **{title}**"
                if date:
                    section += f" ({date})"
                section += "\n"
                if summary:
                    section += f"  {summary}\n"
                section += "\n"
        
        return section
        
    def _generate_company_section(self, result: ResearchResults) -> str:
        """Generate a markdown section for a company with proper null handling.
        
        Args:
            result: Research results for a company
            
        Returns:
            Markdown section for the company
        """
        ticker = result.company_profile.ticker if result.company_profile and hasattr(result.company_profile, 'ticker') else "Unknown"
        name = result.company_profile.name or ticker
        
        section = f"""
### {name} ({ticker})

Financial Health
---------------
| Metric | Value |
|---|---|
"""
        # Add metrics with null handling
        if result.company_profile.gross_margin != 0:
            section += f"| Gross Margin | {result.company_profile.gross_margin:.2f}% |\n"
        else:
            section += "| Gross Margin | N/A |\n"
            
        if result.company_profile.operating_margin != 0:
            section += f"| Operating Margin | {result.company_profile.operating_margin:.2f}% |\n"
        else:
            section += "| Operating Margin | N/A |\n"
            
        if result.company_profile.profit_margin != 0:
            section += f"| Profit Margin | {result.company_profile.profit_margin:.2f}% |\n"
        else:
            section += "| Profit Margin | N/A |\n"
            
        if result.company_profile.pe_ratio > 0:
            section += f"| P/E Ratio | {result.company_profile.pe_ratio:.2f} |\n"
        else:
            section += "| P/E Ratio | N/A |\n"
        
        # Growth Metrics
        section += """
Growth Analysis
--------------
| Metric | Value |
|---|---|
"""
        if result.company_profile.revenue_growth != 0:
            section += f"| Revenue Growth | {result.company_profile.revenue_growth:.2f}% |\n"
        else:
            section += "| Revenue Growth | N/A |\n"
            
        # Stock Performance
        section += """
Stock Performance
----------------
| Metric | Value |
|---|---|
"""
        if result.stock_data:
            if result.stock_data.current_price > 0:
                section += f"| Current Price | ${result.stock_data.current_price:.2f} |\n"
            else:
                section += "| Current Price | N/A |\n"
                
            if result.stock_data.ma_50 > 0:
                section += f"| 50-Day MA | ${result.stock_data.ma_50:.2f} |\n"
            else:
                section += "| 50-Day MA | N/A |\n"
                
            if result.stock_data.ma_200 > 0:
                section += f"| 200-Day MA | ${result.stock_data.ma_200:.2f} |\n"
            else:
                section += "| 200-Day MA | N/A |\n"
                
            if result.stock_data.rsi > 0:
                section += f"| RSI | {result.stock_data.rsi:.2f} |\n"
            else:
                section += "| RSI | N/A |\n"
                
            # Only add historical returns if the attribute exists and has values
            if hasattr(result.stock_data, 'historical_prices') and result.stock_data.historical_prices:
                section += "| Historical Prices | Available |\n"
                
        else:
            section += "| Current Price | N/A |\n"
            section += "| 50-Day MA | N/A |\n"
            section += "| 200-Day MA | N/A |\n"
            section += "| RSI | N/A |\n"
        
        # News Section
        if result.news_data and result.news_data.articles:
            section += """
Recent News
-----------
"""
            # Add up to 3 recent news items
            for i, article in enumerate(result.news_data.articles[:3]):
                title = article.get('title', 'No title')
                date = article.get('date', 'Unknown date')
                url = article.get('url', '')
                
                if url:
                    section += f"- [{title}]({url}) - {date}\n"
                else:
                    section += f"- {title} - {date}\n"
                    
        return section
