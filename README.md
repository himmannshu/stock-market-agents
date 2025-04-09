# Financial Research Agent with Streamlit Interface

This project demonstrates a multi-agent system for generating financial research reports for publicly traded companies, accessible via a Streamlit web interface.

## Overview

The system uses a series of specialized AI agents, orchestrated by a manager, to handle a user's request for financial analysis:

1.  **User Input**: The user enters a company name or ticker symbol through the Streamlit web app.
2.  **Planning**: A `planner_agent` analyzes the request and generates relevant search terms for web searches.
3.  **Financial Data Retrieval**: A `financial_data_agent` uses a custom tool (`financial_data_search`) built on the [Financial Datasets API](https://docs.financialdatasets.ai/introduction) to fetch detailed, structured financial data (historical statements, metrics, news, ownership, trades, etc.). This data is formatted into Markdown tables and lists.
4.  **Web Search**: A `search_agent` uses the built-in `WebSearchTool` to gather broader context, news, and analyst views based on the planned search terms.
5.  **Report Synthesis**: A `writer_agent` receives the detailed financial data and the web search summaries. It synthesizes this information into a comprehensive, detailed Markdown report, incorporating specific figures and details verbatim as instructed by its prompt. It also generates an executive summary and follow-up questions. The `writer_agent` can optionally use tools representing `financials_agent` and `risk_agent` for deeper dives if needed (though the focus is on using the directly provided detailed data).
6.  **Verification**: A `verifier_agent` reviews the generated Markdown report for inconsistencies or potential issues.
7.  **Display**: The Streamlit app (`streamlit_app.py`) displays the final report, executive summary, follow-up questions, and verification results. It also provides a button to download the full report as a Markdown file.

## Features

*   Multi-agent workflow for specialized tasks.
*   Integration with Financial Datasets API for detailed, structured financial data.
*   Web search integration for market context and news.
*   Streamlit web interface for user interaction.
*   Generation of detailed Markdown reports.
*   Report download functionality.

## Setup

1.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd <repository-directory>
    ```
2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    ```
3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Set Up API Keys:**
    *   Copy the `.env.template` file to a new file named `.env`:
        ```bash
        cp .env.template .env
        ```
    *   Obtain an API key from [Financial Datasets](https://financialdatasets.ai) and add it to the `.env` file:
        ```
        FINANCIAL_DATASETS_API_KEY=your_financial_datasets_key_here
        ```
    *   Obtain an API key from [OpenAI](https://platform.openai.com/api-keys) and add it to the `.env` file (or ensure `OPENAI_API_KEY` is set as an environment variable):
        ```
        OPENAI_API_KEY=your_openai_key_here
        # You might also need OPENAI_ORG_ID depending on your setup
        ```

## Running the Application

1.  Ensure your virtual environment is activated.
2.  Run the Streamlit app from the project's root directory:
    ```bash
    streamlit run streamlit_app.py
    ```
3.  The application will open in your web browser. Enter a company name or ticker symbol and click "Analyze".

## Project Structure

```
.
├── financial_agents/ # Contains definitions for individual agents and tools
│   ├── __init__.py
│   ├── financial_data_agent.py
│   ├── financial_data_tool.py
│   ├── financials_agent.py
│   ├── planner_agent.py
│   ├── risk_agent.py
│   ├── search_agent.py
│   ├── verifier_agent.py
│   └── writer_agent.py
├── .env            # API keys (Create from .env.template)
├── .env.template   # Template for API keys
├── .gitignore
├── manager.py      # Orchestrates the agent workflow
├── README.md       # This file
├── requirements.txt # Python dependencies
└── streamlit_app.py # Main Streamlit application file
```
