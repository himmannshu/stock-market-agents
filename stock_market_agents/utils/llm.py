"""LLM helper for processing financial data."""

import logging
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from openai import AsyncOpenAI

from ..models.research import ResearchResults

logger = logging.getLogger(__name__)

class LLMHelper:
    """Helper class for LLM operations."""
    
    def __init__(self):
        """Initialize the LLM helper."""
        self.client = AsyncOpenAI()
        
    def _extract_json(self, text: str) -> str:
        """Extract JSON from text that may contain other content.
        
        Args:
            text: Text that may contain JSON
            
        Returns:
            Extracted JSON string
        """
        # Try to find JSON object
        obj_match = re.search(r'\{(?:[^{}]|(?R))*\}', text)
        if obj_match:
            return obj_match.group(0)
            
        # Try to find JSON array
        arr_match = re.search(r'\[(?:[^\[\]]|(?R))*\]', text)
        if arr_match:
            return arr_match.group(0)
            
        return text
        
    def _parse_json_response(self, response_text: str, default_value: Any) -> Any:
        """Parse JSON response from LLM, handling potential errors.
        
        Args:
            response_text: Text to parse as JSON
            default_value: Default value if parsing fails
            
        Returns:
            Parsed JSON or default value
        """
        try:
            # First try direct parsing
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                pass
                
            # Try to extract and parse JSON
            json_str = self._extract_json(response_text)
            if not json_str:
                logger.error("No JSON found in response")
                return default_value
                
            return json.loads(json_str)
            
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {str(e)}", exc_info=True)
            return default_value
    
    async def break_down_question(self, question: str) -> List[Dict[str, str]]:
        """Break down a complex question into sub-questions.
        
        Args:
            question: Complex question to break down
            
        Returns:
            List of sub-questions with company info
        """
        system_prompt = """You are a financial research assistant. Break down the given question into specific sub-questions that can be researched individually. Focus on key metrics like revenue growth, profit margins, and stock performance. For each sub-question, identify the company being asked about.

CRITICAL: Your response must contain ONLY a valid JSON array of questions, with no additional text or explanations. Each question must be a dictionary with 'question', 'company_name', and 'ticker' fields."""
        
        user_prompt = f"""Break down this question into specific sub-questions: {question}
        
        Return ONLY a JSON array like this, with no additional text:
        [
            {{"question": "What was Apple's revenue growth in Q4 2024?", "company_name": "Apple", "ticker": "AAPL"}},
            {{"question": "How did Microsoft's profit margins change in 2024?", "company_name": "Microsoft", "ticker": "MSFT"}}
        ]"""
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0
            )
            
            sub_questions = self._parse_json_response(response.choices[0].message.content, [])
            logger.info(f"Generated {len(sub_questions)} sub-questions")
            return sub_questions
            
        except Exception as e:
            logger.error(f"Failed to break down question: {str(e)}", exc_info=True)
            return []
    
    async def extract_company_info(self, text: str) -> Dict[str, str]:
        """Extract company information from text.
        
        Args:
            text: Text to extract from
            
        Returns:
            Dictionary with company_name and ticker
        """
        system_prompt = """You are a financial research assistant. Extract company information from the given text. If multiple companies are mentioned, focus on the main company being discussed.

CRITICAL: Your response must contain ONLY a valid JSON object, with no additional text or explanations. The object must have 'company_name' and 'ticker' fields."""
        
        user_prompt = f"""Extract the company name and ticker symbol from this text: {text}
        
        Return ONLY a JSON object like this, with no additional text:
        {{
            "company_name": "Company Name",
            "ticker": "TICK"
        }}"""
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0
            )
            
            return self._parse_json_response(response.choices[0].message.content, {})
            
        except Exception as e:
            logger.error(f"Failed to extract company info: {str(e)}", exc_info=True)
            return {}
    
    async def analyze_results(self, question: str, sub_questions: List[Dict[str, str]], results: List[ResearchResults]) -> Dict[str, Any]:
        """Analyze research results to generate insights.
        
        Args:
            question: Original question
            sub_questions: List of sub-questions
            results: List of research results
            
        Returns:
            Analysis results
        """
        system_prompt = """You are a financial analyst. Analyze the research results to generate insights, comparisons, limitations, and recommendations. Focus on key metrics and trends.

CRITICAL: Your response must contain ONLY a valid JSON object with these fields, with no additional text or explanations:
- insights: List of key insights (strings)
- comparisons: List of comparative points (strings)
- limitations: List of data limitations (strings)
- recommendations: List of actionable recommendations (strings)
- confidence: Confidence score (float between 0 and 1)"""
        
        # Prepare research data for each company
        research_data = {}
        for result in results:
            if not result.company_profile:
                continue
                
            ticker = result.company_profile.ticker
            research_data[ticker] = {
                "profile": {
                    "name": result.company_profile.name,
                    "sector": result.company_profile.sector,
                    "industry": result.company_profile.industry,
                    "market_cap": result.company_profile.market_cap,
                    "pe_ratio": result.company_profile.pe_ratio,
                    "profit_margin": result.company_profile.profit_margin,
                    "revenue_growth": result.company_profile.revenue_growth
                },
                "financials": {
                    "revenue": result.financial_metrics.total_revenue if result.financial_metrics else [],
                    "net_income": result.financial_metrics.net_income if result.financial_metrics else [],
                    "eps": result.financial_metrics.eps if result.financial_metrics else []
                },
                "stock": {
                    "current_price": result.stock_data.current_price if result.stock_data else 0,
                    "high_52week": result.stock_data.high_52week if result.stock_data else 0,
                    "low_52week": result.stock_data.low_52week if result.stock_data else 0,
                    "rsi": result.stock_data.rsi if result.stock_data else 0,
                    "beta": result.stock_data.beta if result.stock_data else 0,
                    "volatility": result.stock_data.volatility if result.stock_data else 0
                }
            }
        
        user_prompt = f"""Analyze these research results for the question: {question}

Research Data:
{json.dumps(research_data, indent=2)}

Return ONLY a JSON object like this, with no additional text:
{{
    "insights": ["Key insight 1", "Key insight 2"],
    "comparisons": ["Comparison point 1", "Comparison point 2"],
    "limitations": ["Limitation 1", "Limitation 2"],
    "recommendations": ["Recommendation 1", "Recommendation 2"],
    "confidence": 0.85
}}"""
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2
            )
            
            analysis = self._parse_json_response(response.choices[0].message.content, {
                "insights": ["Analysis failed"],
                "comparisons": [],
                "limitations": ["Error processing results"],
                "recommendations": [],
                "confidence": 0
            })
            logger.info("Completed analysis")
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze results: {str(e)}", exc_info=True)
            return {
                "insights": ["Analysis failed"],
                "comparisons": [],
                "limitations": ["Error processing results"],
                "recommendations": [],
                "confidence": 0
            }
