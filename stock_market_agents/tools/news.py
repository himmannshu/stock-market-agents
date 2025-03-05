"""News search tool using Tavily API."""

import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from tavily import AsyncTavilyClient

logger = logging.getLogger(__name__)

class NewsTool:
    """Tool for searching news articles using Tavily."""
    
    def __init__(self):
        """Initialize the news tool."""
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY environment variable not set")
        self.client = AsyncTavilyClient(api_key)
        
    async def search_company_news(self, company_name: str, ticker: str) -> List[Dict[str, Any]]:
        """Search for recent news about a company.
        
        Args:
            company_name: Name of the company
            ticker: Stock ticker symbol
            
        Returns:
            List of news articles with summaries
        """
        try:
            # Search for company news from the last month
            query = f"{company_name} ({ticker}) stock financial news"
            response = await self.client.search(
                query=query,
                search_depth="advanced",
                include_answer=True,
                include_raw_content=True,
                max_results=10
            )
            
            # Process and format results
            articles = []
            for result in response.get("results", []):
                article = {
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "published_date": result.get("published_date", ""),
                    "content": result.get("content", ""),
                    "summary": result.get("summary", ""),
                    "sentiment": result.get("sentiment", "neutral")
                }
                articles.append(article)
            
            # Add analysis summary
            analysis = response.get("answer", {})
            if analysis:
                articles.append({
                    "type": "analysis",
                    "content": analysis
                })
            
            logger.info(f"Found {len(articles)} news articles for {company_name}")
            return articles
            
        except Exception as e:
            logger.error(f"Failed to search news: {str(e)}", exc_info=True)
            return []
