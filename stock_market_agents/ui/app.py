"""Gradio UI for Stock Market Analysis."""

import os
import sys
import logging
from pathlib import Path
from typing import Tuple, List
import asyncio
import gradio as gr

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from stock_market_agents.agents.manager_agent import ManagerAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s',
    handlers=[
        logging.StreamHandler(),  # Log to console
        logging.FileHandler('app.log')  # Log to file
    ]
)
logger = logging.getLogger(__name__)

class StockAnalysisUI:
    """Gradio UI for Stock Market Analysis."""
    
    def __init__(self):
        """Initialize the UI components."""
        self.manager = ManagerAgent()
        self.logs = []
        
    def add_log(self, message: str) -> None:
        """Add a log message to the log list.
        
        Args:
            message: Log message to add
        """
        self.logs.append(message)
        
    async def analyze_stocks(self, question: str) -> Tuple[str, str]:
        """Analyze stocks based on user question.
        
        Args:
            question: User's question about stocks
            
        Returns:
            Tuple of (markdown report content, logs)
        """
        try:
            # Clear previous logs
            self.logs = []
            self.add_log(f"Received question: {question}")
            
            # Research the question
            self.add_log("Starting research...")
            analysis_results, report_path = await self.manager.research(question)
            
            # Read the report
            self.add_log(f"Research complete. Reading report from {report_path}")
            with open(report_path, 'r') as f:
                report_content = f.read()
                
            self.add_log("Analysis complete!")
            return report_content, "\n".join(self.logs)
            
        except Exception as e:
            error_msg = f"Error analyzing stocks: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.add_log(error_msg)
            return "", "\n".join(self.logs)
    
    def launch(self) -> None:
        """Launch the Gradio UI."""
        # Create the interface
        with gr.Blocks(title="Stock Market Analysis") as demo:
            gr.Markdown("""
            # Stock Market Analysis
            
            Ask questions about stocks and get detailed analysis reports. Examples:
            - Compare Apple and Microsoft's financial performance
            - Analyze Tesla's revenue growth and profit margins
            - How has Amazon's stock performed over the past year?
            """)
            
            with gr.Tab("Analysis"):
                question = gr.Textbox(
                    label="Your Question",
                    placeholder="Enter your question about stocks...",
                    lines=2
                )
                analyze_btn = gr.Button("Analyze")
                
                with gr.Row():
                    # Report display with download button
                    report = gr.Markdown(
                        label="Analysis Report",
                        show_label=True
                    )
                    
                    # Download button for the report
                    download_btn = gr.Button("📥 Download Report")
            
            with gr.Tab("Logs"):
                logs = gr.Textbox(
                    label="Analysis Logs",
                    show_label=True,
                    lines=20,
                    max_lines=50,
                    interactive=False
                )
            
            # Handle events
            analyze_btn.click(
                fn=lambda q: asyncio.run(self.analyze_stocks(q)),
                inputs=[question],
                outputs=[report, logs]
            )
            
            # Download handler
            def save_report(report_content: str) -> str:
                """Save report content to a file and return the path."""
                if not report_content:
                    return None
                    
                # Save to a new file
                timestamp = asyncio.run(self.manager.get_timestamp())
                filename = f"financial_analysis_{timestamp}.md"
                filepath = os.path.join("reports", filename)
                
                with open(filepath, "w") as f:
                    f.write(report_content)
                    
                return filepath
                
            download_btn.click(
                fn=save_report,
                inputs=[report],
                outputs=[gr.File(label="Download Report")]
            )
        
        # Launch the app
        demo.launch()
