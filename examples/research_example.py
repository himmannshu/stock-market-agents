"""Example of using the stock market research agents"""
import os
import asyncio
import logging
from stock_market_agents.agents.manager_agent import ManagerAgent
from dotenv import load_dotenv
# Set up logging
logger = logging.getLogger(__name__)

async def main():
    """Run an example research task"""
    # Load environment variables
    load_dotenv()
    
    # Get API keys from environment
    alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not alpha_vantage_key:
        raise ValueError("Please set ALPHA_VANTAGE_API_KEY environment variable")
    
    # Initialize manager agent
    manager = ManagerAgent(alpha_vantage_key)
    
    # Example research question
    question = "How does Apple's financial performance compare to Microsoft's over the past year? Consider revenue growth, profit margins, and stock performance."
    
    try:
        # Run research
        logger.info("Starting research task")
        result = await manager.research(question)
        
        # Print results
        print("\nResearch Results:")
        print("================")
        print(f"\nQuestion: {result['question']}")
        print("\nSub-questions:")
        for i, q in enumerate(result['sub_questions'], 1):
            print(f"{i}. {q['question']}")
            if q['company_name']:
                print(f"   Company: {q['company_name']} ({q['ticker']})")
        
        print("\nAnalysis:")
        print("=========")
        print(f"\nSummary: {result['analysis']['summary']}")
        print("\nDetailed Analysis:")
        print(result['analysis']['detailed_analysis'])
        print(f"\nConfidence: {result['analysis']['confidence']:.0%}")
        
        if result['analysis']['limitations']:
            print("\nLimitations:")
            for limitation in result['analysis']['limitations']:
                print(f"- {limitation}")
        
        print("\nSources:")
        for source in result['analysis']['sources']:
            print(f"- {source}")
            
    except Exception as e:
        logger.error(f"Research failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main())
