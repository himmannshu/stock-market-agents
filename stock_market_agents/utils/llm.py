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
        # First, analyze the question to understand what metrics are being requested
        analysis_prompt = f"""Analyze this financial question and identify:
1. The specific metrics or aspects being asked about
2. The companies mentioned
3. Any time periods or comparison points
4. The context or purpose of the analysis

Question: {question}

Return ONLY a JSON object with these fields:
{{
    "metrics": ["list of specific metrics requested"],
    "companies": ["list of companies mentioned"],
    "time_periods": ["list of time periods mentioned"],
    "context": "brief description of analysis purpose"
}}"""

        try:
            # Get question analysis
            analysis_response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a financial analysis expert. Analyze the question and return ONLY a JSON object with the specified fields."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.2
            )
            
            analysis = self._parse_json_response(analysis_response.choices[0].message.content, {
                "metrics": [],
                "companies": [],
                "time_periods": [],
                "context": ""
            })
            
            # Now generate specific sub-questions based on the analysis
            sub_questions_prompt = f"""Based on this analysis:
{json.dumps(analysis, indent=2)}

Generate specific sub-questions that will help answer the original question: {question}

Requirements:
1. Each sub-question should focus on a specific metric or aspect
2. Include time periods if specified
3. Make comparisons if multiple companies are mentioned
4. Consider the analysis context
5. Include both quantitative and qualitative aspects

Return ONLY a JSON array of sub-questions, each with:
{{
    "question": "specific sub-question",
    "company_name": "company name",
    "ticker": "company ticker if known",
    "metric": "specific metric being asked about",
    "time_period": "time period if specified"
}}"""

            # Generate sub-questions
            sub_questions_response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a financial research expert. Generate specific sub-questions based on the analysis and return ONLY a JSON array."},
                    {"role": "user", "content": sub_questions_prompt}
                ],
                temperature=0.3  # Slightly higher temperature for more variety
            )
            
            sub_questions = self._parse_json_response(sub_questions_response.choices[0].message.content, [])
            
            # Validate and clean up sub-questions
            validated_questions = []
            for q in sub_questions:
                # Ensure required fields
                if not q.get("question") or not q.get("company_name"):
                    continue
                    
                # Try to get ticker if not provided
                if not q.get("ticker"):
                    company_info = await self.extract_company_info(q["company_name"])
                    q["ticker"] = company_info.get("ticker", "")
                
                validated_questions.append(q)
            
            logger.info(f"Generated {len(validated_questions)} validated sub-questions")
            return validated_questions
            
        except Exception as e:
            logger.error(f"Failed to break down question: {str(e)}", exc_info=True)
            # Fallback to basic pattern matching if LLM fails
            company_patterns = [
                r"(?:analyze|research|examine|study|investigate)\s+([A-Za-z0-9\s]+?)'s",
                r"(?:analyze|research|examine|study|investigate)\s+([A-Za-z0-9\s]+)\s+(?:revenue|profit|growth|stock|share|performance)",
                r"([A-Za-z0-9\s]+)'s\s+(?:revenue|profit|growth|stock|share|performance)",
                r"([A-Za-z0-9\s]+)\s+(?:revenue|profit|growth|stock|share|performance)",
            ]
            
            for pattern in company_patterns:
                match = re.search(pattern, question)
                if match:
                    company_name = match.group(1).strip()
                    company_info = await self.extract_company_info(company_name)
                    ticker = company_info.get("ticker", "")
                    
                    # Generate more focused sub-questions based on the original question
                    metrics = ["revenue growth", "profit margins", "financial performance", "stock performance"]
                    if "revenue" in question.lower():
                        metrics = ["revenue growth", "revenue trends", "revenue by segment"]
                    elif "profit" in question.lower():
                        metrics = ["profit margins", "operating margins", "net income"]
                    elif "stock" in question.lower():
                        metrics = ["stock price", "stock performance", "trading volume"]
                    
                    return [
                        {
                            "question": f"What is {company_name}'s {metric}?",
                            "company_name": company_name,
                            "ticker": ticker,
                            "metric": metric
                        }
                        for metric in metrics
                    ]
            
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
