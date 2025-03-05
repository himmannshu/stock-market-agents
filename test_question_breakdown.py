import asyncio
import logging
from stock_market_agents.utils.llm import LLMHelper
from stock_market_agents.agents.manager_agent import ManagerAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_question_breakdown():
    try:
        # Initialize manager agent
        manager = ManagerAgent()
        
        # Test questions with different complexity levels
        test_questions = [
            # Simple question about revenue and profit
            "analyze Tesla's revenue growth and profit margins",
            
            # Complex question about technical indicators
            "What are Tesla's technical indicators including RSI, MACD, and moving averages?",
            
            # Question about fundamental analysis
            "Analyze Tesla's fundamental metrics including P/E ratio, PEG ratio, and dividend yield",
            
            # Question about economic impact
            "How do economic indicators affect Tesla's stock performance?"
        ]
        
        for question in test_questions:
            print(f"\nTesting question: {question}")
            print("=" * 50)
            
            # Get sub-questions
            sub_questions = await manager.llm_helper.break_down_question(question)
            
            # Print sub-questions
            print("\nGenerated Sub-questions:")
            print("========================")
            for i, q in enumerate(sub_questions, 1):
                print(f"\n{i}. Question: {q['question']}")
                print(f"   Company: {q['company_name']}")
                print(f"   Ticker: {q['ticker']}")
                print(f"   Metric: {q.get('metric', 'N/A')}")
                print(f"   Time Period: {q.get('time_period', 'N/A')}")
            
            # Test the research process
            print("\nTesting Research Process:")
            print("=========================")
            research_results = await manager.researcher.research_concurrent(sub_questions)
            
            # Print research results
            for i, result in enumerate(research_results, 1):
                print(f"\nResearch Result {i}:")
                print(f"Question: {result.question}")
                if result.company_profile:
                    print(f"Company: {result.company_profile.name} ({result.company_profile.ticker})")
                    print(f"Metrics available:")
                    if hasattr(result.company_profile, 'rsi'):
                        print(f"- RSI: {result.company_profile.rsi}")
                    if hasattr(result.company_profile, 'macd'):
                        print(f"- MACD: {result.company_profile.macd}")
                    if hasattr(result.company_profile, 'peg_ratio'):
                        print(f"- PEG Ratio: {result.company_profile.peg_ratio}")
                    if hasattr(result.company_profile, 'dividend_yield'):
                        print(f"- Dividend Yield: {result.company_profile.dividend_yield}")
                if result.error:
                    print(f"Error: {result.error}")
            
            print("\n" + "=" * 50)
            
    except Exception as e:
        logger.error(f"Error in test: {str(e)}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_question_breakdown()) 