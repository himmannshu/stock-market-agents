"""LLM helper for natural language processing tasks"""
import json
import logging
from openai import AsyncOpenAI
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class LLMHelper:
    """Helper class for LLM operations"""
    
    def __init__(self):
        """Initialize the LLM helper"""
        self.client = AsyncOpenAI()
    
    async def break_down_question(self, question: str) -> List[Dict[str, str]]:
        """Break down a complex question into simpler sub-questions
        
        Args:
            question: Complex question to break down
            
        Returns:
            List of sub-questions with optional company info
        """
        try:
            logger.debug(f"Breaking down question: {question}")
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert at breaking down complex financial questions into simpler sub-questions.
Your task is to break down the given question into 2-4 specific sub-questions that can be researched independently.
For each sub-question, try to identify the company name and ticker symbol if present.

Format your response as a JSON array of objects, where each object has these fields:
- question: The sub-question text
- company_name: Company name (if present in the sub-question)
- ticker: Stock ticker symbol (if present in the sub-question)

Example:
For the question "Compare Apple and Microsoft's revenue growth":
[
    {
        "question": "What was Apple's revenue growth in the past year?",
        "company_name": "Apple",
        "ticker": "AAPL"
    },
    {
        "question": "What was Microsoft's revenue growth in the past year?",
        "company_name": "Microsoft",
        "ticker": "MSFT"
    }
]"""
                    },
                    {
                        "role": "user",
                        "content": question
                    }
                ],
                temperature=0.7
            )
            
            result = response.choices[0].message.content
            logger.debug(f"LLM response: {result}")
            
            # Parse JSON response
            sub_questions = json.loads(result)
            logger.info(f"Generated {len(sub_questions)} sub-questions")
            return sub_questions
            
        except Exception as e:
            logger.error(f"Failed to break down question: {str(e)}")
            # Return original question as single sub-question
            return [{"question": question, "company_name": None, "ticker": None}]
    
    async def extract_company_info(self, text: str) -> Dict[str, Optional[str]]:
        """Extract company name and ticker from text
        
        Args:
            text: Text to extract from
            
        Returns:
            Dict with company_name and ticker
        """
        try:
            logger.debug(f"Extracting company info from: {text}")
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert at identifying company names and their stock ticker symbols in text.
Your task is to extract the company name and ticker symbol from the given text.
If multiple companies are mentioned, focus on the most relevant one for financial analysis.

Format your response as a JSON object with these fields:
- company_name: The company name (or null if not found)
- ticker: The stock ticker symbol (or null if not found)

Example:
For "What is Apple's revenue?":
{
    "company_name": "Apple",
    "ticker": "AAPL"
}"""
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                temperature=0.7
            )
            
            result = response.choices[0].message.content
            logger.debug(f"LLM response: {result}")
            
            # Parse JSON response
            company_info = json.loads(result)
            logger.info(f"Extracted company info: {company_info}")
            return company_info
            
        except Exception as e:
            logger.error(f"Failed to extract company info: {str(e)}")
            return {"company_name": None, "ticker": None}
    
    def _extract_key_metrics(self, data: Dict[str, Any], company: str) -> Dict[str, Any]:
        """Extract key metrics from financial data
        
        Args:
            data: Raw financial data
            company: Company name
            
        Returns:
            Dict with key metrics
        """
        metrics = {
            "company": company,
            "overview": {},
            "income": {},
            "stock": {}
        }
        
        # Extract overview metrics
        if "overview" in data:
            overview = data["overview"]
            metrics["overview"] = {
                "MarketCap": overview.get("MarketCapitalization"),
                "PERatio": overview.get("PERatio"),
                "ProfitMargin": overview.get("ProfitMargin"),
                "Industry": overview.get("Industry")
            }
        
        # Extract income statement metrics
        if "income_statement" in data:
            income = data["income_statement"]
            if "annualReports" in income and len(income["annualReports"]) >= 2:
                current = income["annualReports"][0]
                previous = income["annualReports"][1]
                
                current_revenue = float(current.get("totalRevenue", 0))
                previous_revenue = float(previous.get("totalRevenue", 0))
                revenue_growth = ((current_revenue - previous_revenue) / previous_revenue) * 100
                
                metrics["income"] = {
                    "RevenueGrowth": f"{revenue_growth:.2f}%",
                    "GrossProfit": current.get("grossProfit"),
                    "NetIncome": current.get("netIncome")
                }
        
        # Extract stock performance metrics
        if "stock_performance" in data:
            stock = data["stock_performance"]
            if "Time Series (Daily)" in stock:
                daily_data = stock["Time Series (Daily)"]
                dates = sorted(daily_data.keys())
                if len(dates) >= 2:
                    latest = float(daily_data[dates[0]]["4. close"])
                    earliest = float(daily_data[dates[-1]]["4. close"])
                    price_change = ((latest - earliest) / earliest) * 100
                    
                    metrics["stock"] = {
                        "PriceChange": f"{price_change:.2f}%",
                        "CurrentPrice": f"${latest:.2f}",
                        "Volume": daily_data[dates[0]].get("5. volume", "N/A")
                    }
        
        return metrics
    
    async def analyze_results(self, question: str, sub_questions: List[Dict[str, str]], results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze research results to form a comprehensive answer
        
        Args:
            question: Original question
            sub_questions: List of sub-questions
            results: Research results for each sub-question
            
        Returns:
            Analysis results
        """
        try:
            logger.debug("Analyzing research results")
            
            # Extract key metrics for each company
            metrics = {}
            for q, r in zip(sub_questions, results):
                company = q.get("company_name")
                if company and r:
                    metrics[company] = self._extract_key_metrics(r, company)
            
            # Create a concise summary for the LLM
            summary = {
                "question": question,
                "metrics": metrics
            }
            
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert financial analyst.
Your task is to analyze financial metrics and provide a comprehensive answer to the original question.

Format your response as a JSON object with these fields:
- summary: Brief summary of findings (1-2 sentences)
- detailed_analysis: Detailed analysis with specific data points
- confidence: Confidence score (0.0 to 1.0) based on data quality
- limitations: List of limitations or missing information
- sources: List of data sources used"""
                    },
                    {
                        "role": "user",
                        "content": json.dumps(summary, indent=2)
                    }
                ],
                temperature=0.7
            )
            
            result = response.choices[0].message.content
            logger.debug(f"LLM response: {result}")
            
            # Parse JSON response
            analysis = json.loads(result)
            logger.info("Analysis complete")
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze results: {str(e)}")
            return {
                "summary": "Analysis failed due to error",
                "detailed_analysis": str(e),
                "confidence": 0.0,
                "limitations": ["Analysis failed"],
                "sources": []
            }
