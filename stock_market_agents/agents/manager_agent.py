"""Manager Agent for coordinating research and analysis"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
from .base_agent import BaseAgent
from .researcher_agent import ResearcherAgent, ResearchResults
from .writer_agent import WriterAgent
from ..utils.llm import LLMHelper

logger = logging.getLogger(__name__)

@dataclass
class CompanyAnalysis:
    """Comprehensive analysis of a company"""
    name: str
    ticker: str
    sector: str
    market_cap: float
    financial_health: Dict[str, Any]  # Key metrics and scores
    growth_metrics: Dict[str, Any]  # Growth rates for different metrics
    stock_analysis: Dict[str, Any]  # Stock performance analysis
    risk_metrics: Dict[str, Any]  # Risk and volatility metrics
    peer_comparison: Optional[Dict[str, Any]] = None  # Comparison with peers if available
    data_timestamp: datetime = None

@dataclass
class AnalysisResults:
    """Results of the manager's analysis"""
    question: str
    company_results: Dict[str, ResearchResults]
    key_insights: List[str]
    comparison_points: List[str]
    limitations: List[str]
    recommendations: List[str]
    data_sources: List[str]
    confidence_score: float
    analysis_time: datetime

class ManagerAgent(BaseAgent):
    """Agent responsible for coordinating research tasks"""
    
    def __init__(self):
        """Initialize the manager agent"""
        super().__init__()
        self.researcher = ResearcherAgent()
        self.writer = WriterAgent()
        self.llm_helper = LLMHelper()
        logger.info("Initialized ManagerAgent")
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the manager agent
        
        Returns:
            System prompt string
        """
        return """You are a financial analysis manager responsible for coordinating research tasks.
Your goal is to break down complex financial questions into specific research tasks and analyze the results.

Follow these steps:
1. Break down complex questions into specific sub-questions
2. Extract company names and tickers from questions
3. Analyze research results to form comprehensive answers
4. Calculate key metrics and trends
5. Compare companies when relevant
6. Identify risks and opportunities
7. Generate actionable insights
8. Note limitations and data quality issues

Remember to:
- Be thorough in your analysis
- Support conclusions with specific data points
- Consider multiple aspects of financial analysis
- Provide clear and actionable insights
- Prepare data for visualization
- Include confidence scores for insights
- Note data freshness and sources
"""
    
    def _get_available_tools(self) -> List[Dict[str, str]]:
        """Get list of available tools for this agent
        
        Returns:
            List of tool descriptions
        """
        return [
            {
                "name": "break_down_question",
                "description": "Break down a complex question into specific sub-questions",
                "parameters": {
                    "question": "The main question to break down"
                }
            },
            {
                "name": "analyze_results",
                "description": "Analyze research results to form a comprehensive answer",
                "parameters": {
                    "question": "The original question",
                    "sub_questions": "List of sub-questions",
                    "results": "Research results for each sub-question"
                }
            }
        ]

    def _analyze_financial_health(self, results: ResearchResults) -> Dict[str, Any]:
        """Analyze company's financial health
        
        Args:
            results: Research results for a company
            
        Returns:
            Financial health metrics and scores
        """
        try:
            if not results.financial_metrics or not results.balance_sheet:
                return {}
            
            # Calculate key ratios
            current_ratio = (
                results.balance_sheet.cash_and_equivalents[0] / 
                results.balance_sheet.total_liabilities[0] * 100  # Convert to percentage
                if results.balance_sheet.total_liabilities[0] != 0 
                else 0
            )
            
            debt_to_equity = (
                results.balance_sheet.total_debt[0] / 
                (results.balance_sheet.total_assets[0] - results.balance_sheet.total_liabilities[0])
                if (results.balance_sheet.total_assets[0] - results.balance_sheet.total_liabilities[0]) != 0
                else 0
            )
            
            return {
                "profitability": {
                    "gross_margin": results.company_profile.gross_margin if results.company_profile else 0,
                    "operating_margin": results.company_profile.operating_margin if results.company_profile else 0,
                    "profit_margin": results.company_profile.profit_margin if results.company_profile else 0
                },
                "liquidity": {
                    "current_ratio": current_ratio,
                    "cash_position": results.balance_sheet.cash_and_equivalents[0]
                },
                "solvency": {
                    "debt_to_equity": debt_to_equity,
                    "total_debt": results.balance_sheet.total_debt[0]
                },
                "efficiency": {
                    "revenue_per_asset": (
                        results.financial_metrics.total_revenue[0] / results.balance_sheet.total_assets[0]
                        if results.balance_sheet.total_assets[0] != 0
                        else 0
                    )
                }
            }
        except Exception as e:
            logger.error(f"Failed to analyze financial health: {str(e)}", exc_info=True)
            return {}
    
    def _analyze_growth(self, results: ResearchResults) -> Dict[str, Any]:
        """Analyze company's growth metrics
        
        Args:
            results: Research results for a company
            
        Returns:
            Growth metrics and trends
        """
        try:
            if not results.financial_metrics:
                return {}
            
            def calculate_growth_rate(values: List[float], periods: int = 1) -> float:
                """Calculate growth rate over specified periods
                
                Args:
                    values: List of values in chronological order (newest first)
                    periods: Number of periods to calculate growth over
                
                Returns:
                    Growth rate as percentage
                """
                if len(values) <= periods:
                    return 0
                
                current = values[0]  # Most recent value
                previous = values[periods]  # Value 'periods' ago
                
                if previous == 0 or current == 0:
                    return 0
                
                growth = ((current - previous) / abs(previous)) * 100
                # Cap extreme values at ±100%
                return max(min(growth, 100), -100)
            
            # Calculate quarterly and annual growth rates
            revenue = results.financial_metrics.total_revenue
            net_income = results.financial_metrics.net_income
            
            revenue_quarterly = [calculate_growth_rate(revenue[i:], 1) for i in range(len(revenue)-1)]
            revenue_annual = calculate_growth_rate(revenue, 4)
            
            profit_quarterly = [calculate_growth_rate(net_income[i:], 1) for i in range(len(net_income)-1)]
            profit_annual = calculate_growth_rate(net_income, 4)
            
            return {
                "revenue": {
                    "quarterly_growth": revenue_quarterly,
                    "annual_growth": revenue_annual,
                    "ttm_growth": results.company_profile.revenue_growth if results.company_profile else 0
                },
                "earnings": {
                    "quarterly_growth": profit_quarterly,
                    "annual_growth": profit_annual,
                    "eps_trend": results.financial_metrics.eps
                }
            }
        except Exception as e:
            logger.error(f"Failed to analyze growth: {str(e)}", exc_info=True)
            return {}
    
    def _analyze_stock_performance(self, results: ResearchResults) -> Dict[str, Any]:
        """Analyze stock performance
        
        Args:
            results: Research results for a company
            
        Returns:
            Stock performance analysis
        """
        try:
            if not results.stock_performance:
                return {}
            
            # Get price trends
            df = results.stock_performance.daily_prices
            
            # Calculate moving averages
            df["ma_50"] = df["close"].rolling(window=50).mean()
            df["ma_200"] = df["close"].rolling(window=200).mean()
            
            # Calculate momentum indicators
            df["rsi"] = self._calculate_rsi(df["close"])
            
            latest_price = df["close"].iloc[-1]
            ma_50 = df["ma_50"].iloc[-1]
            ma_200 = df["ma_200"].iloc[-1]
            
            return {
                "current_price": latest_price,
                "price_changes": results.stock_performance.price_changes,
                "volume_analysis": {
                    "average_volume": results.stock_performance.volume_avg,
                    "volume_trend": "up" if df["volume"].iloc[-5:].mean() > results.stock_performance.volume_avg else "down"
                },
                "technical_indicators": {
                    "ma_50": ma_50,
                    "ma_200": ma_200,
                    "trend": "bullish" if ma_50 > ma_200 else "bearish",
                    "rsi": df["rsi"].iloc[-1]
                },
                "volatility": results.stock_performance.volatility
            }
        except Exception as e:
            logger.error(f"Failed to analyze stock performance: {str(e)}", exc_info=True)
            return {}
    
    def _calculate_rsi(self, prices: pd.Series, periods: int = 14) -> pd.Series:
        """Calculate Relative Strength Index
        
        Args:
            prices: Price series
            periods: RSI period
            
        Returns:
            RSI values
        """
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))
        except Exception:
            return pd.Series(index=prices.index)
    
    def _analyze_risk(self, results: ResearchResults) -> Dict[str, Any]:
        """Analyze company risk metrics
        
        Args:
            results: Research results for a company
            
        Returns:
            Risk analysis
        """
        try:
            if not results.company_profile or not results.stock_performance:
                return {}
            
            return {
                "market_risk": {
                    "beta": results.company_profile.beta,
                    "volatility": results.stock_performance.volatility
                },
                "financial_risk": {
                    "debt_level": "high" if results.balance_sheet and results.balance_sheet.total_debt[0] > results.balance_sheet.total_assets[0] * 0.5 else "moderate",
                    "interest_coverage": None  # Would need additional data
                },
                "valuation_risk": {
                    "pe_ratio": results.company_profile.pe_ratio,
                    "price_to_book": None  # Would need additional data
                }
            }
        except Exception as e:
            logger.error(f"Failed to analyze risk: {str(e)}", exc_info=True)
            return {}
    
    def _create_company_analysis(self, results: ResearchResults) -> Optional[CompanyAnalysis]:
        """Create comprehensive company analysis
        
        Args:
            results: Research results for a company
            
        Returns:
            Company analysis or None if insufficient data
        """
        try:
            if not results.company_profile:
                return None
            
            return CompanyAnalysis(
                name=results.company_profile.name,
                ticker=results.company_profile.ticker,
                sector=results.company_profile.sector,
                market_cap=results.company_profile.market_cap,
                financial_health=self._analyze_financial_health(results),
                growth_metrics=self._analyze_growth(results),
                stock_analysis=self._analyze_stock_performance(results),
                risk_metrics=self._analyze_risk(results),
                data_timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"Failed to create company analysis: {str(e)}", exc_info=True)
            return None
    
    async def research(self, question: str) -> Tuple[AnalysisResults, str]:
        """Research a financial question and generate analysis.
        
        Args:
            question: Question to research
            
        Returns:
            Tuple of (AnalysisResults, markdown_report)
        """
        try:
            # Generate sub-questions
            sub_questions = await self.llm_helper.break_down_question(question)
            logger.info(f"Generated {len(sub_questions)} sub-questions")
            
            # Research each sub-question
            research_results = await self.researcher.research_concurrent(sub_questions)
            logger.info("Completed research for all sub-questions")
            
            # Group results by company
            company_results = {}
            for result in research_results:
                if result.company_profile and result.company_profile.ticker:
                    company_results[result.company_profile.ticker] = result
            
            # Analyze results
            analysis = await self.llm_helper.analyze_results(question, sub_questions, research_results)
            
            # Create analysis results
            analysis_results = AnalysisResults(
                question=question,
                company_results=company_results,
                key_insights=analysis.get("insights", []),
                comparison_points=analysis.get("comparisons", []),
                limitations=analysis.get("limitations", []),
                recommendations=analysis.get("recommendations", []),
                data_sources=["Alpha Vantage API", "SEC Filings"],
                confidence_score=analysis.get("confidence", 0.0),
                analysis_time=datetime.now()
            )
            
            # Generate report
            report = await self.writer.generate_report(analysis_results)
            logger.info("Generated markdown report")
            
            return analysis_results, report
            
        except Exception as e:
            logger.error(f"Research failed: {str(e)}", exc_info=True)
            raise
