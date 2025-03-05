"""Web search tool using Tavily API for financial research."""

import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from tavily import AsyncTavilyClient

logger = logging.getLogger(__name__)

class WebSearchTool:
    """Tool for searching web content using Tavily."""
    
    def __init__(self):
        """Initialize the web search tool."""
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
            logger.info(f"Searching for news with query: {query}")
            
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
                # Extract article details with proper fallback values
                title = result.get("title", "No title available")
                url = result.get("url", "")
                published_date = result.get("published_date", "")
                
                # If published_date is empty, use a placeholder
                if not published_date:
                    published_date = "Recent"
                
                # Extract content and create a summary if not present
                content = result.get("content", "")
                summary = result.get("summary", "")
                
                # If summary is empty but we have content, create a shorter summary
                if not summary and content:
                    summary = content[:200] + "..." if len(content) > 200 else content
                elif not summary:
                    summary = "No summary available"
                
                # Basic sentiment analysis based on content if not provided
                sentiment = result.get("sentiment", "neutral")
                
                article = {
                    "title": title,
                    "url": url,
                    "published_date": published_date,
                    "summary": summary,
                    "sentiment": sentiment
                }
                articles.append(article)
            
            # Add analysis summary from Tavily
            analysis = response.get("answer", "")
            if analysis:
                # Create an analysis entry with the aggregated information
                articles.append({
                    "title": f"{company_name} News Analysis",
                    "url": "",
                    "published_date": "Analysis",
                    "summary": analysis,
                    "sentiment": "neutral",
                    "type": "analysis"
                })
            
            logger.info(f"Found {len(articles)} news articles for {company_name}")
            
            # Fallback for empty results - create a generic entry 
            if not articles:
                articles = [{
                    "title": f"{company_name} Financial Information",
                    "url": f"https://finance.yahoo.com/quote/{ticker}",
                    "published_date": "Current",
                    "summary": f"No specific news articles were found for {company_name}. This may be due to API limitations or rate limiting.",
                    "sentiment": "neutral"
                }]
                
            return articles
            
        except Exception as e:
            logger.error(f"Failed to search news: {str(e)}", exc_info=True)
            # Return a fallback result on error
            return [{
                "title": f"Error Retrieving {company_name} News",
                "url": "",
                "published_date": "Error",
                "summary": f"An error occurred while retrieving news: {str(e)}. This may be due to API rate limiting or network issues.",
                "sentiment": "neutral"
            }]
    
    async def search_financial_metrics(self, company_name: str, ticker: str, metric_type: str) -> Dict[str, Any]:
        """Search for specific financial metrics or analysis.
        
        Args:
            company_name: Name of the company
            ticker: Stock ticker symbol
            metric_type: Type of metric/analysis (e.g., 'revenue', 'growth', 'competitors', 'forecast')
            
        Returns:
            Dictionary containing search results and analysis
        """
        try:
            # Create a targeted query based on the metric type
            query = f"{company_name} ({ticker}) {metric_type} financial analysis"
            logger.info(f"Searching for {metric_type} information on {company_name}")
            
            response = await self.client.search(
                query=query,
                search_depth="advanced",
                include_answer=True,
                include_raw_content=True,
                max_results=5
            )
            
            # Extract key information
            search_results = {
                "query": query,
                "results": [],
                "analysis": response.get("answer", "No analysis available")
            }
            
            for result in response.get("results", []):
                search_results["results"].append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "summary": result.get("summary", ""),
                    "content": result.get("content", "")[:500] + "..." # Truncate content
                })
            
            logger.info(f"Found {len(search_results['results'])} results for {metric_type} search on {company_name}")
            return search_results
            
        except Exception as e:
            logger.error(f"Failed to search {metric_type} information: {str(e)}", exc_info=True)
            return {"query": "", "results": [], "analysis": f"Error: {str(e)}"}
    
    async def search_market_sentiment(self, company_name: str, ticker: str) -> Dict[str, Any]:
        """Search for market sentiment and expert opinions.
        
        Args:
            company_name: Name of the company
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with sentiment analysis results
        """
        try:
            query = f"{company_name} ({ticker}) stock market sentiment analyst opinions"
            logger.info(f"Searching for market sentiment on {company_name}")
            
            response = await self.client.search(
                query=query,
                search_depth="advanced",
                include_answer=True,
                max_results=7
            )
            
            sentiment_data = {
                "overall_sentiment": "",
                "analyst_opinions": [],
                "summary": response.get("answer", "")
            }
            
            # Try to extract sentiment from the results
            if response.get("results"):
                # Extract analyst opinions
                for result in response.get("results", []):
                    if "opinion" in result.get("title", "").lower() or "analyst" in result.get("title", "").lower():
                        sentiment_data["analyst_opinions"].append({
                            "source": result.get("title", ""),
                            "url": result.get("url", ""),
                            "summary": result.get("summary", "")
                        })
            
            # Determine overall sentiment based on the answer
            answer = response.get("answer", "").lower()
            if "positive" in answer or "bullish" in answer or "buy" in answer:
                sentiment_data["overall_sentiment"] = "positive"
            elif "negative" in answer or "bearish" in answer or "sell" in answer:
                sentiment_data["overall_sentiment"] = "negative"
            else:
                sentiment_data["overall_sentiment"] = "neutral"
                
            logger.info(f"Completed sentiment analysis for {company_name}")
            return sentiment_data
            
        except Exception as e:
            logger.error(f"Failed to get market sentiment: {str(e)}", exc_info=True)
            return {
                "overall_sentiment": "unknown",
                "analyst_opinions": [],
                "summary": f"Error: {str(e)}"
            }
            
# Backward compatibility
NewsTool = WebSearchTool
