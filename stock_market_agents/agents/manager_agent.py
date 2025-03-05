"""Manager agent for coordinating research and report generation."""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from .base_agent import BaseAgent
from .researcher_agent import ResearcherAgent
from .writer_agent import WriterAgent
from ..utils.llm import LLMHelper
from ..models.research import AnalysisResults, ResearchResults

logger = logging.getLogger(__name__)

class ManagerAgent(BaseAgent):
    """Agent for managing research and report generation."""
    
    def __init__(self):
        """Initialize the manager agent."""
        super().__init__()
        self.researcher = ResearcherAgent()
        self.writer = WriterAgent()
        self.llm_helper = LLMHelper()
        logger.info("Initialized ManagerAgent")
        
    def _get_system_prompt(self) -> str:
        """Get the system prompt for this agent.
        
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
        """Get list of available tools for this agent.
        
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
        
    async def get_timestamp(self) -> str:
        """Get a formatted timestamp for filenames.
        
        Returns:
            Formatted timestamp string
        """
        return datetime.now().strftime("%Y%m%d_%H%M%S")
        
    async def research(self, question: str) -> Tuple[AnalysisResults, str]:
        """Research a financial question and generate analysis.
        
        Args:
            question: Question to research
            
        Returns:
            Tuple of (AnalysisResults, report_path)
        """
        try:
            logger.info(f"Starting research for question: {question}")
            
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
            timestamp = await self.get_timestamp()
            report_path = f"reports/financial_analysis_{timestamp}.md"
            
            # Ensure reports directory exists
            os.makedirs("reports", exist_ok=True)
            
            # Write report
            await self.writer.write_report(
                question=question,
                results=research_results,
                analysis=analysis,
                output_path=report_path
            )
            logger.info("Generated markdown report")
            
            return analysis_results, report_path
            
        except Exception as e:
            logger.error(f"Error in research pipeline: {str(e)}", exc_info=True)
            raise
