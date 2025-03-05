"""Example script demonstrating the full research pipeline."""

import asyncio
import logging
import os
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from stock_market_agents.agents.manager_agent import ManagerAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s'
)

async def main():
    """Run the research pipeline example."""
    try:
        logger = logging.getLogger(__name__)
        logger.info("Starting research task")
        
        # Initialize manager agent
        manager = ManagerAgent()
        
        # Example research question
        question = "How does Apple's financial performance compare to Microsoft's over the past year? Consider revenue growth, profit margins, and stock performance."
        
        # Run research pipeline
        analysis, report = await manager.research(question)
        
        # Save report to file
        output_dir = Path("reports")
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = output_dir / f"financial_analysis_{timestamp}.md"
        
        with open(report_path, "w") as f:
            f.write(report)
            
        logger.info(f"Report saved to: {report_path}")
        
        # Print report to console
        print("\nGenerated Report:")
        print("================\n")
        print(report)
        
    except Exception as e:
        logger.error(f"Failed to run example: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    asyncio.run(main())
