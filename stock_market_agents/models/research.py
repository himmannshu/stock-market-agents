"""Data models for research and analysis results."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class CompanyProfile:
    """Company profile data."""
    name: str
    ticker: str
    sector: str
    industry: str
    market_cap: float
    pe_ratio: float
    gross_margin: float
    operating_margin: float
    profit_margin: float
    revenue_growth: float

@dataclass
class FinancialMetrics:
    """Financial metrics data."""
    total_revenue: List[float]
    net_income: List[float]
    eps: List[float]
    periods: List[str]

@dataclass
class BalanceSheet:
    """Balance sheet data."""
    total_assets: List[float]
    total_liabilities: List[float]
    total_debt: List[float]
    cash_and_equivalents: List[float]
    periods: List[str]

@dataclass
class StockData:
    """Stock price and performance data."""
    current_price: float
    high_52week: float
    low_52week: float
    volume: float
    rsi: float
    ma_50: float
    ma_200: float
    beta: float
    volatility: float
    historical_prices: Optional[List[float]] = None

@dataclass
class CompanyAnalysis:
    """Comprehensive analysis for a company."""
    company_name: str
    ticker: str
    financial_health: Dict[str, Any]
    growth_metrics: Dict[str, Any]
    stock_performance: Dict[str, Any]
    risk_assessment: Dict[str, Any]

@dataclass
class ResearchResults:
    """Results from researching a specific question."""
    question: str
    company_profile: CompanyProfile
    financial_metrics: FinancialMetrics
    balance_sheet: BalanceSheet
    stock_data: StockData
    error: Optional[str] = None

@dataclass
class AnalysisResults:
    """Complete analysis results."""
    question: str
    company_results: Dict[str, ResearchResults]  # Key is company ticker
    key_insights: List[str]
    comparison_points: List[str]
    limitations: List[str]
    recommendations: List[str]
    data_sources: List[str]
    confidence_score: float
    analysis_time: datetime
