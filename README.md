# Stock Market Agents

A Python project that provides intelligent agents for analyzing stock market data using the Alpha Vantage API, SEC filings, and LLM capabilities.

## Features

- **Multi-Agent System**: Coordinated agents for research, analysis, and report generation
  - Manager Agent: Orchestrates research tasks and generates comprehensive reports
  - Researcher Agent: Gathers and processes financial data from multiple sources
  - Writer Agent: Formats analysis results into well-structured markdown reports
- **Financial Data Integration**:
  - Alpha Vantage API for real-time market data
  - SEC EDGAR database for company filings
  - Semantic search for intelligent endpoint discovery using ChromaDB
- **Comprehensive Analysis**:
  - Revenue growth and profit margins
  - Stock performance metrics (RSI, Beta, Volatility)
  - Technical indicators (Moving Averages)
  - Comparative analysis between companies
- **LLM Integration**: OpenAI's GPT models for:
  - Breaking down complex financial questions
  - Analyzing research results
  - Generating insights and recommendations
- **Web Search**: Tavily integration for real-time market research

## Installation

1. Clone the repository:
```bash
git clone https://github.com/himmannshu/stock-market-agents.git
cd stock-market-agents
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Set up your environment variables:
```bash
# Create a .env file with your API keys
ALPHA_VANTAGE_API_KEY=your_api_key_here
OPENAI_API_KEY=your_openai_key_here
TAVILY_API_KEY=your_tavily_key_here
SEC_API_KEY=your_sec_api_key
```

## Usage

```python
python run_ui.py
```

### Example: Financial Research

```python
from stock_market_agents.agents.manager_agent import ManagerAgent

# Initialize the manager agent
manager = ManagerAgent()

# Research a financial question
question = "Compare Apple and Microsoft's financial performance"
report = await manager.research(question)

# The report will be saved in the reports/ directory
print(f"Report saved to: {report}")
```

### Example: Custom Research

```python
from stock_market_agents.agents.researcher_agent import ResearcherAgent

# Initialize the researcher agent
researcher = ResearcherAgent()

# Research specific aspects
results = await researcher.research_question({
    "question": "What was Apple's revenue growth?",
    "company_name": "Apple",
    "ticker": "AAPL"
})

# Access the research results
print(f"Revenue Growth: {results.financial_metrics.revenue_growth}")
print(f"Profit Margin: {results.company_profile.profit_margin}")
```

## Project Structure

```
stock-market-agents/
├── stock_market_agents/
│   ├── agents/
│   │   ├── manager_agent.py
│   │   ├── researcher_agent.py
│   │   └── writer_agent.py
│   ├── models/
│   │   └── research.py
│   ├── tools/
│   │   ├── alpha_vantage.py
│   │   └── sec.py
│   └── utils/
│       └── llm.py
├── examples/
│   └── research_example.py
├── tests/
├── reports/  # Generated markdown reports
└── README.md
```

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Running Examples

```bash
python examples/research_example.py
```

### Adding New Features

1. Create a new branch for your feature
2. Implement your changes
3. Add tests
4. Submit a pull request

## Dependencies

Core dependencies (see `requirements.txt` for full list):
- `openai`: For LLM integration
- `chromadb`: For semantic search
- `tavily-python`: For web search
- `pandas`: For data processing
- `matplotlib`: For generating charts
- `requests`: For API calls

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request
