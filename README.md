# Stock Sentiment Analysis Platform

A comprehensive stock sentiment analysis platform that aggregates and analyzes market sentiment from multiple sources including Yahoo Finance news and SEC filings. The platform uses natural language processing and machine learning to provide insights into market sentiment for specific stocks.

## Features

- Real-time stock data analysis using Yahoo Finance
- SEC filings sentiment analysis
- News sentiment analysis using FinBERT
- Interactive web interface built with Streamlit
- Multi-source data aggregation
- Sentiment visualization and analytics

## Prerequisites

- Python >=3.10 <3.13
- SEC API token (for SEC filings analysis)
- Ollama model: deepseek-r1:7b

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd stock-sentiment-analysis
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with your API keys:
```
SEC_API_TOKEN=your_sec_api_token
```

## Running the Application

1. Start the Streamlit application:
```bash
streamlit run src/agentic_market_analysis/app.py
```

2. Open your browser and navigate to `http://localhost:8501`

## Usage

1. Navigate to the "Sentiment Analysis" tab
2. Enter a query like "What is the sentiment towards Apple stock?"
3. Click "Analyze Query" to see the results
4. View sentiment distribution and detailed analysis in the interface

## Project Structure

- `src/agentic_market_analysis/`
  - `agents.py`: Contains the Yahoo Finance and SEC filing analysis agents
  - `app.py`: Streamlit web interface
  - `chat_inference.py`: Query parsing and intent extraction
  - `orchestration.py`: Data collection and aggregation logic

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
