import asyncio
import logging
from typing import List, Dict, Any
from .base_agent import BaseAgent
from .researcher_agent import ResearcherAgent
from ..utils.llm import LLMHelper

logger = logging.getLogger(__name__)

class ManagerAgent(BaseAgent):
    """Agent responsible for coordinating research tasks"""
    
    def __init__(self, api_key: str):
        """Initialize the manager agent
        
        Args:
            api_key: Alpha Vantage API key
        """
        super().__init__()
        self.researcher = ResearcherAgent(api_key)
        self.llm = LLMHelper()
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
4. Highlight key insights and patterns
5. Note any limitations or missing information

Remember to:
- Be thorough in your analysis
- Support conclusions with specific data points
- Consider multiple aspects of financial analysis
- Provide clear and actionable insights
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
    
    async def research(self, question: str) -> Dict[str, Any]:
        """Research a complex question by breaking it down and coordinating research
        
        Args:
            question: Complex question to research
            
        Returns:
            Research results and analysis
        """
        logger.info(f"Starting research for question: {question}")
        
        try:
            # Break down complex question into sub-questions
            logger.debug("Breaking down question into sub-questions")
            sub_questions = await self.llm.break_down_question(question)
            logger.info(f"Generated {len(sub_questions)} sub-questions")
            
            # Research all sub-questions concurrently
            logger.debug("Starting concurrent research")
            results = await self.researcher.research_multiple(sub_questions)
            logger.info("Completed research for all sub-questions")
            
            # Analyze and combine results
            logger.debug("Analyzing research results")
            analysis = await self.llm.analyze_results(question, sub_questions, results)
            logger.info("Completed analysis")
            
            response = {
                "question": question,
                "sub_questions": sub_questions,
                "results": results,
                "analysis": analysis
            }
            
            # Log detailed response at debug level
            logger.debug("Research response: %s", response)
            
            return response
            
        except Exception as e:
            logger.error(f"Research failed: {str(e)}", exc_info=True)
            raise
