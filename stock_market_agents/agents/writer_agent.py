"""Writer Agent for generating markdown reports from financial analysis.

This agent is responsible for:
1. Taking analysis results from the Manager Agent
2. Generating well-structured markdown reports
3. Adding visualizations and formatting
4. Ensuring consistent style and readability
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..models.research import AnalysisResults, ResearchResults
from ..utils.markdown import (
    create_header,
    create_table,
    create_chart,
    format_currency,
    format_percentage
)

logger = logging.getLogger(__name__)

class WriterAgent:
    """Agent for generating markdown reports from financial analysis."""
    
    def __init__(self):
        """Initialize the WriterAgent."""
        logger.info("Initialized WriterAgent")
        
    async def generate_report(self, analysis: AnalysisResults) -> str:
        """Generate a markdown report from analysis results.
        
        Args:
            analysis: Analysis results from the Manager Agent
            
        Returns:
            Markdown formatted report
        """
        try:
            report_sections = []
            
            # Add report header
            report_sections.append(self._generate_header(analysis))
            
            # Add company analysis sections
            for company_name, results in analysis.company_results.items():
                report_sections.append(self._generate_company_section(company_name, results))
            
            return "\n\n".join(report_sections)
            
        except Exception as e:
            logger.error(f"Failed to generate report: {str(e)}", exc_info=True)
            return f"Error generating report: {str(e)}"
    
    def _generate_header(self, analysis: AnalysisResults) -> str:
        """Generate the report header.
        
        Args:
            analysis: Analysis results
            
        Returns:
            Markdown formatted header
        """
        header = [
            create_header("Financial Analysis Report", level=1),
            "",
            f"Analysis Time: {analysis.analysis_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Companies Analyzed: {', '.join(analysis.company_results.keys())}",
            f"Confidence Score: {format_percentage(analysis.confidence_score)}",
            f"Data Sources: {', '.join(analysis.data_sources)}",
            "",
            create_header("Executive Summary", level=2),
            "",
            "Key Insights:",
            *[f"- {insight}" for insight in analysis.key_insights],
            "",
            "Comparative Analysis:",
            *[f"- {point}" for point in analysis.comparison_points],
            "",
            "Limitations:",
            *[f"- {limitation}" for limitation in analysis.limitations],
            "",
            "Recommendations:",
            *[f"- {recommendation}" for recommendation in analysis.recommendations],
            "",
            create_header("Company Analysis", level=2),
            ""
        ]
        return "\n".join(header)
    
    def _generate_company_section(self, company_name: str, results: ResearchResults) -> str:
        """Generate a company analysis section.
        
        Args:
            company_name: Name of the company
            results: Research results for the company
            
        Returns:
            Markdown formatted company section
        """
        section = [
            create_header(f"{results.company_profile.name} ({company_name})", level=3),
            "",
            "Financial Health",
            "---------------",
        ]
        
        # Add financial metrics table
        if results.company_profile:
            metrics_table = {
                "Metric": ["Gross Margin", "Operating Margin", "Profit Margin"],
                "Value": [
                    format_percentage(results.company_profile.gross_margin),
                    format_percentage(results.company_profile.operating_margin),
                    format_percentage(results.company_profile.profit_margin)
                ]
            }
            section.extend([
                create_table(metrics_table),
                ""
            ])
        
        # Add growth analysis
        if results.financial_metrics:
            section.extend([
                "Growth Analysis",
                "--------------",
                f"Revenue Growth (TTM): {format_percentage(results.company_profile.revenue_growth)}",
                "",
                "Quarterly Revenue Growth:",
                create_table({
                    "Quarter": [f"Q{i+1}" for i in range(len(results.financial_metrics.total_revenue[:4]))],
                    "Revenue": [format_currency(rev) for rev in results.financial_metrics.total_revenue[:4]]
                }),
                ""
            ])
        
        # Add stock performance
        if results.stock_data:
            section.extend([
                "Stock Performance",
                "----------------",
                f"Current Price: {format_currency(results.stock_data.current_price)}",
                f"52-Week High: {format_currency(results.stock_data.high_52week)}",
                f"52-Week Low: {format_currency(results.stock_data.low_52week)}",
                f"RSI: {results.stock_data.rsi:.2f}",
                f"Beta: {results.stock_data.beta:.2f}",
                f"Volatility: {format_percentage(results.stock_data.volatility)}",
                ""
            ])
            
            # Add price chart if we have historical data
            if results.stock_data.historical_prices:
                price_data = {
                    "Price": results.stock_data.historical_prices[:30],  # Last 30 days
                    "MA50": [results.stock_data.ma_50] * 30,
                    "MA200": [results.stock_data.ma_200] * 30
                }
                section.extend([
                    create_chart(
                        title=f"{company_name} Stock Price",
                        data=price_data,
                        chart_type="line"
                    ),
                    ""
                ])
        
        return "\n".join(section)
