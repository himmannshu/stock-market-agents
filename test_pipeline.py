import asyncio
import logging
import tempfile
import os
from stock_market_agents.agents.researcher_agent import ResearcherAgent
from stock_market_agents.agents.manager_agent import ManagerAgent
from stock_market_agents.agents.writer_agent import WriterAgent

logging.basicConfig(level=logging.INFO)

async def test_pipeline():
    try:
        # ManagerAgent creates its own instances of ResearcherAgent and WriterAgent
        manager = ManagerAgent()
        
        question = 'How is Apple (AAPL) performing financially?'
        
        print(f"Running analysis for question: {question}")
        # The research method doesn't take an output_dir parameter
        analysis_results, report_path = await manager.research(question)
        
        print(f'Successfully generated report at {report_path}')
        
        # Print some of the key data points from the analysis
        # Analysis results is an AnalysisResults object with attributes, not a dictionary
        if analysis_results and hasattr(analysis_results, 'company_results'):
            for ticker, data in analysis_results.company_results.items():
                print(f"\nKey insights for {ticker}:")
                
                # Test if the specific analysis sections exist
                analysis_data = {}
                if 'company_results' in analysis_results.__dict__:
                    analysis_data = analysis_results.company_results.get(ticker, {})
                
                # Print available analysis information
                print(f"Company: {ticker}")
                print(f"Question: {analysis_results.question}")
                print(f"Key insights: {', '.join(analysis_results.key_insights[:3])} ...")
                print(f"Confidence score: {analysis_results.confidence_score}")
                    
        print("\nTest completed successfully!")
        
    except Exception as e:
        print(f'Error: {str(e)}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_pipeline())
