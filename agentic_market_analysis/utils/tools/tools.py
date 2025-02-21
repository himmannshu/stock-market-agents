import os
import requests 

from langchain_core.tools import tool
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from dotenv import load_dotenv

load_dotenv()

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
vector_store = Chroma(
    collection_name='alpha_vantage_api_rules',
    embedding_function=embeddings,
    persist_directory='./agentic_market_analysis/db/'
)

@tool
def retrieve_alpha_vantage_api_endpoint(query: str):
    retrieved_docs = vector_store.similarity_search(query)
    return {"context": retrieved_docs, "question": query}

@tool
def call_alpha_vantage_api(url_endpoint: str, parameters: dict):
    """
    Tool function to call the Alpha Vantage API for a given endpoint and parameters.

    Args:
        endpoint_name: The name of the API endpoint to call (e.g., "get_stock_price").
        parameters: A dictionary of parameters for the API call (e.g., {"symbol": "AAPL"}).
        api_rules_file: Path to the JSON file containing API rules.

    Returns:
        A dictionary representing the JSON response from the API, or an error message.
    """

    api_key = os.environ.get("ALPHA_VANTAGE_API_KEY") # Get API Key from environment variable - SECURE!
    if not api_key:
        return {"error": "ALPHA_VANTAGE_API_KEY environment variable not set. Please set your API key."}

    # Construct the full URL with parameters
    url = f"{url_endpoint}"
    params = parameters.copy() # Create a copy to avoid modifying original dict
    params['apikey'] = api_key

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        return response.json() # Return JSON response as a dictionary
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {e}"}
    
@tool
def generate_financial_report(report_summary: str, sources: list) -> str:
    """
    Tool function to generate a financial report in a readable format.

    Args:
        report_summary: A summary of the financial findings (string).
        sources: A list of Alpha Vantage API endpoint names used as sources.

    Returns:
        A formatted report string.
    """
    report = "Financial Report:\n\n"
    report += report_summary + "\n\n"
    report += "Data Sources:\n"
    for source in sources:
        report += f"- Alpha Vantage API Endpoint: {source}\n"
    report += "\n***End of Report***"
    return report
