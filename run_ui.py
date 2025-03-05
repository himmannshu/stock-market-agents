"""Launch the Stock Market Analysis UI."""

import asyncio
from stock_market_agents.ui.app import StockAnalysisUI

def main():
    """Run the UI application."""
    # Create and launch the UI
    app = StockAnalysisUI()
    app.launch()

if __name__ == "__main__":
    main()
