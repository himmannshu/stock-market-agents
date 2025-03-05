"""Gradio UI for Stock Market Analysis."""

import os
import sys
import logging
from pathlib import Path
from typing import Tuple, List
import asyncio
import gradio as gr
import time
from datetime import datetime
import queue
import threading

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from stock_market_agents.agents.manager_agent import ManagerAgent

# Configure custom log handler that puts logs into a queue for the UI to consume.
class QueueHandler(logging.Handler):
    """Handler that puts logs into a queue for the UI to consume."""
    
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue
        
    def emit(self, record):
        try:
            msg = self.format(record)
            self.log_queue.put(msg)
        except Exception:
            self.handleError(record)

# Configure logging
log_queue = queue.Queue()
queue_handler = QueueHandler(log_queue)
queue_handler.setFormatter(
    logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
)

file_handler = logging.FileHandler('app.log')
file_handler.setFormatter(
    logging.Formatter('%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s')
)

console_handler = logging.StreamHandler()
console_handler.setFormatter(
    logging.Formatter('%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s')
)

# Configure the root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Clear any existing handlers to avoid duplicates
for handler in list(root_logger.handlers):
    root_logger.removeHandler(handler)

# Add our handlers
root_logger.addHandler(queue_handler)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# Get a logger for this module
logger = logging.getLogger(__name__)
logger.info("Logging configured for Stock Analysis UI")

# Make sure all other loggers use our configuration
for name in logging.root.manager.loggerDict:
    logger_instance = logging.getLogger(name)
    logger_instance.setLevel(logging.INFO)
    # Avoid duplicate handlers
    for handler in list(logger_instance.handlers):
        logger_instance.removeHandler(handler)
    # Use propagation to root logger instead of direct handlers
    logger_instance.propagate = True

class StockAnalysisUI:
    """Gradio UI for Stock Market Analysis."""
    
    def __init__(self):
        """Initialize the UI components."""
        self.manager = ManagerAgent()
        self.log_queue = log_queue
        self.analysis_running = False
        logger.info("Stock Analysis UI initialized")
    
    def get_logs(self) -> str:
        """Get all logs from the queue.
        
        Returns:
            String with all logs
        """
        logs = []
        try:
            while not self.log_queue.empty():
                logs.append(self.log_queue.get_nowait())
        except queue.Empty:
            pass
        
        log_text = "\n".join(logs)
        logger.debug(f"Retrieved {len(logs)} log entries")
        return log_text
    
    async def stream_logs(self) -> str:
        """Stream logs periodically while analysis is running.
        
        Yields:
            Current logs as they arrive
        """
        while self.analysis_running:
            logs = self.get_logs()
            if logs:
                yield logs
            await asyncio.sleep(0.5)
        
        # Final yield to get any remaining logs
        final_logs = self.get_logs()
        if final_logs:
            yield final_logs
    
    async def analyze_stocks(self, question: str) -> Tuple[str, str]:
        """Analyze stocks based on user question.
        
        Args:
            question: User's question about stocks
            
        Returns:
            Tuple of (markdown report content, logs)
        """
        try:
            # Set analysis flag
            self.analysis_running = True
            
            # Log the question
            logger.info(f"Received question: {question}")
            
            # Research the question
            logger.info("Starting research...")
            analysis_results, report_path = await self.manager.research(question)
            
            # Read the report
            logger.info(f"Research complete. Reading report from {report_path}")
            with open(report_path, 'r') as f:
                report_content = f.read()
                
            logger.info("Analysis complete!")
            
            # Set analysis flag
            self.analysis_running = False
            
            # Get final logs
            logs = self.get_logs()
            
            return report_content, logs
            
        except Exception as e:
            error_msg = f"Error analyzing stocks: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.analysis_running = False
            logs = self.get_logs()
            return "", logs
    
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
                    interactive=False,
                    autoscroll=True
                )
                
                # Add a refresh button for logs
                refresh_logs_btn = gr.Button("🔄 Refresh Logs")
            
            # Handle events and add real-time log updates
            def start_analysis(question):
                # Clear previous logs from the UI when starting a new analysis
                return None, ""
                
            # Use a two-step process for updating logs
            analyze_btn.click(
                fn=start_analysis,
                inputs=[question],
                outputs=[report, logs]
            ).then(
                fn=lambda q: asyncio.run(self.analyze_stocks(q)),
                inputs=[question],
                outputs=[report, logs]
            )
            
            # Create a real-time log updating mechanism while analysis is running
            async def update_logs():
                while True:
                    log_text = self.get_logs()
                    yield log_text
                    if not self.analysis_running:
                        break
                    await asyncio.sleep(0.5)
            
            # Add real-time log updating during analysis
            analyze_btn.click(
                fn=lambda: gr.Textbox.update(value="Starting analysis...", lines=20),
                inputs=[],
                outputs=[logs]
            ).then(
                fn=update_logs,
                inputs=[],
                outputs=[logs]
            )
            
            # Add manual log refresh
            refresh_logs_btn.click(
                fn=self.get_logs,
                inputs=[],
                outputs=[logs]
            )
            
            # Download handler
            def save_report(report_content: str) -> str:
                """Save report content to a file and return the path."""
                if not report_content:
                    return None
                    
                # Save to a new file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"financial_analysis_{timestamp}.md"
                filepath = os.path.join("reports", filename)
                
                # Ensure reports directory exists
                os.makedirs("reports", exist_ok=True)
                
                with open(filepath, "w") as f:
                    f.write(report_content)
                    
                return filepath
                
            download_btn.click(
                fn=save_report,
                inputs=[report],
                outputs=[gr.File(label="Download Report")]
            )
        
        # Launch the app
        demo.queue()
        demo.launch()
