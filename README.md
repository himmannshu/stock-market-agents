# Stock Market Agents

A Python project that provides intelligent agents for interacting with stock market data using the Alpha Vantage API and LLM capabilities.

## Features

- **Alpha Vantage API Integration**: Seamless integration with Alpha Vantage's comprehensive financial data API
- **Documentation Scraping**: Automatic scraping and parsing of Alpha Vantage API documentation
- **Semantic Search**: Intelligent endpoint discovery using ChromaDB for semantic search
- **LLM Integration**: Integration with OpenAI's GPT models for intelligent query processing
- **Web Search Capabilities**: Integration with Tavily for real-time market research

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
```

## Usage

### Alpha Vantage Tool

The `AlphaVantageTool` class provides a powerful interface for interacting with the Alpha Vantage API:

```python
from stock_market_agents.tools.alpha_vantage import AlphaVantageTool

# Initialize the tool
tool = AlphaVantageTool(api_key="your_api_key")

# Scrape and embed API documentation
endpoints = tool.scrape_documentation()
tool.embed_documentation(endpoints)

# Query for relevant endpoints
results = tool.query("How to get stock price data?")

# Make API calls
data = tool.call_endpoint(
    function="TIME_SERIES_DAILY",
    symbol="GOOGL"
)
```

### Jupyter Notebook Integration

The project includes Jupyter notebook examples demonstrating:
- Setting up the environment
- Using the Alpha Vantage tool
- Integrating with LLM models
- Performing market research

## Project Structure

```
stock-market-agents/
├── stock_market_agents/
│   └── tools/
│       └── alpha_vantage.py
├── tests/
│   └── test_alpha_vantage.py
├── notebooks/
│   └── stock_market_agent.ipynb
├── requirements.txt
└── README.md
```

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Adding New Features

1. Create a new branch for your feature
2. Implement your changes
3. Add tests
4. Submit a pull request

## Dependencies

- `requests`: For making HTTP requests
- `beautifulsoup4`: For parsing HTML documentation
- `chromadb`: For semantic search capabilities
- `openai`: For LLM integration
- `tavily-python`: For web search capabilities
- Other dependencies listed in `requirements.txt`

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

