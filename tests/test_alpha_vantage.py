import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stock_market_agents.tools.alpha_vantage import AlphaVantageTool
from bs4 import BeautifulSoup
import requests

def print_endpoint_details(endpoint):
    """Print details about an API endpoint."""
    print(f"\n{endpoint['name']}")
    if endpoint.get('description'):
        print(f"   Description: {endpoint['description']}")
    print(f"   Function: {endpoint['function']}")
    print(f"   Required params: {list(endpoint.get('required_params', {}).keys())}")
    print(f"   Optional params: {list(endpoint.get('optional_params', {}).keys())}")
    if endpoint.get('example_response'):
        print(f"   Example response: {endpoint['example_response'][:200]}...")

def test_alpha_vantage_tool():
    """Test the Alpha Vantage tool's functionality."""
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        raise ValueError("Please set the ALPHA_VANTAGE_API_KEY environment variable")
    
    tool = AlphaVantageTool(api_key=api_key)
    
    print("\n=== Testing Documentation Scraping ===")
    endpoints = tool.scrape_documentation()
    print(f"Found {len(endpoints)} endpoints")
    
    print("\n=== Example Endpoints ===")
    for i, endpoint in enumerate(endpoints[:3], 1):
        print(f"\n{i}. {endpoint.name}")
        print(f"   Description: {endpoint.description}")
        print(f"   Function: {endpoint.function}")
        print(f"   Required params: {list(endpoint.required_params.keys())}")
        print(f"   Optional params: {list(endpoint.optional_params.keys())}")
    
    print("\n=== Testing Documentation Embedding ===")
    print("Creating embeddings for API documentation...")
    tool.embed_documentation(endpoints)
    
    print("\nTesting query: 'How to get stock price data?'")
    results = tool.query("How to get stock price data?", top_k=3)
    for result in results:
        print_endpoint_details(result)

if __name__ == "__main__":
    test_alpha_vantage_tool() 