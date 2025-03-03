import os
import json
import requests
from bs4 import BeautifulSoup
import chromadb
from typing import Dict, List, Optional, Union, Tuple, Any
from dataclasses import dataclass
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class APIEndpoint:
    """Data class to store API endpoint information"""
    name: str
    description: str
    endpoint: str
    function: str
    required_params: Dict[str, str]
    optional_params: Dict[str, str]
    example_response: Optional[str] = None

class AlphaVantageTool:
    """Tool for interacting with Alpha Vantage API"""
    
    def __init__(self, api_key: str, collection_name: str = "alpha_vantage_endpoints"):
        """Initialize the Alpha Vantage tool
        
        Args:
            api_key: Alpha Vantage API key
            collection_name: Name for the ChromaDB collection
        """
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.docs_url = "https://www.alphavantage.co/documentation/"
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(collection_name)
    
    def _get_documentation_html(self) -> str:
        """Get the documentation HTML content"""
        try:
            response = requests.get(self.docs_url, timeout=10)
            response.raise_for_status()
            html_content = response.text
            
            # Create a data directory if it doesn't exist
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
            os.makedirs(data_dir, exist_ok=True)
            
            # Save the HTML content
            html_file = os.path.join(data_dir, "alpha_vantage_docs.html")
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(html_content)
                logger.info(f"Saved documentation to {html_file}")
            
            return html_content
        except requests.RequestException as e:
            logger.error(f"Error fetching documentation: {e}")
            raise
        except IOError as e:
            logger.error(f"Error saving documentation: {e}")
            raise
    
    def scrape_documentation(self, use_saved_html: bool = False) -> List[APIEndpoint]:
        """Scrape the Alpha Vantage documentation and extract endpoint information
        
        Args:
            use_saved_html: Whether to use a locally saved HTML file instead of fetching from the web
        """
        logger.info("Scraping Alpha Vantage documentation...")
        
        try:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
            html_file = os.path.join(data_dir, "alpha_vantage_docs.html")
            
            if use_saved_html and os.path.exists(html_file):
                with open(html_file, "r", encoding="utf-8") as f:
                    html_content = f.read()
                    logger.info(f"Using saved HTML from {html_file}")
            else:
                html_content = self._get_documentation_html()
            
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Find the main content article
            main_content = soup.find("article", class_="main-content")
            if not main_content:
                logger.error("Could not find main content section")
                return []
            
            # Find all API endpoints (h4 tags)
            endpoints = []
            for endpoint_header in main_content.find_all("h4"):
                # Skip if this is not an API endpoint (e.g., if it's a subsection header)
                header_text = endpoint_header.get_text(strip=True)
                if not header_text or "API Parameters" in header_text or "Examples" in header_text:
                    continue
                
                # Get the function name (first word, removing any labels)
                function_name = header_text.split()[0].strip()
                # Remove any labels like "Trending" or "Premium"
                function_name = re.sub(r'(Trending|Premium)$', '', function_name)
                
                # Get the description (p tag after h4)
                description = ""
                next_elem = endpoint_header.find_next_sibling()
                while next_elem and next_elem.name == "br":
                    next_elem = next_elem.find_next_sibling()
                if next_elem and next_elem.name == "p":
                    description = next_elem.get_text(strip=True)
                
                # Get the endpoint URL from example section
                endpoint_url = ""
                example_section = None
                current = endpoint_header
                while current:
                    current = current.find_next_sibling()
                    if current and current.name == "h4":
                        break
                    if current and current.name == "h6" and "Examples" in current.get_text():
                        example_section = current
                        break
                
                if example_section:
                    # Find the first code block after the Examples header
                    code_block = example_section.find_next("code")
                    if code_block:
                        text = code_block.get_text(strip=True)
                        if "query?function=" in text:
                            endpoint_url = text
                
                # Extract parameters
                required_params = {}
                optional_params = {}
                
                # Find parameter section
                param_section = None
                current = endpoint_header
                while current:
                    current = current.find_next_sibling()
                    if current and current.name == "h4":
                        break
                    if current and current.name == "h6" and "API Parameters" in current.get_text():
                        param_section = current
                        break
                
                if param_section:
                    # Process parameters
                    current = param_section
                    while current:
                        current = current.find_next_sibling()
                        if not current or current.name == "h4" or (current.name == "h6" and "Examples" in current.get_text()):
                            break
                        
                        if current.name == "p":
                            text = current.get_text(strip=True)
                            if text.startswith("❚"):
                                # This is a parameter definition
                                is_required = "Required:" in text
                                param_name = None
                                code_tag = current.find("code")
                                if code_tag:
                                    param_name = code_tag.get_text(strip=True)
                                
                                # Get the description from the next p tag
                                desc_tag = current.find_next_sibling("p")
                                if desc_tag and param_name:
                                    param_desc = desc_tag.get_text(strip=True)
                                    if is_required:
                                        required_params[param_name] = param_desc
                                    else:
                                        optional_params[param_name] = param_desc
                
                # Get example response from the code blocks
                example_response = None
                code_blocks = endpoint_header.find_next("div", class_="python-code")
                if code_blocks:
                    code = code_blocks.find("code")
                    if code:
                        text = code.get_text(strip=True)
                        if "{" in text and "}" in text:
                            try:
                                # Clean up the text to make it valid JSON
                                cleaned_text = re.sub(r'([{,])\s*([a-zA-Z_]+):', r'\1"\2":', text)
                                json.loads(cleaned_text)
                                example_response = cleaned_text
                            except json.JSONDecodeError:
                                pass
                
                if function_name and endpoint_url:  # Only add if we have the essential information
                    endpoint = APIEndpoint(
                        name=function_name,
                        description=description,
                        endpoint=endpoint_url,
                        function=function_name,
                        required_params=required_params,
                        optional_params=optional_params,
                        example_response=example_response
                    )
                    endpoints.append(endpoint)
            
            logger.info(f"Found {len(endpoints)} API endpoints")
            return endpoints
            
        except Exception as e:
            logger.error(f"Error scraping documentation: {e}")
            raise
    
    def _clean_description(self, description: str) -> str:
        """Clean and format parameter descriptions"""
        desc = description.strip()
        desc = re.sub(r'\s+', ' ', desc)  # Replace multiple spaces with single space
        desc = re.sub(r'[\\n\\r]+', ' ', desc)  # Remove newlines
        desc = re.sub(r'\(\s*e\.g\.,?\s*', '(e.g., ', desc)  # Clean up examples
        desc = re.sub(r'\(\s*example:?\s*', '(example: ', desc)
        return desc
    
    def embed_documentation(self, endpoints: List[APIEndpoint]) -> None:
        """Create embeddings for the API documentation.
        
        Args:
            endpoints: List of API endpoints to embed
        """
        logger.info("Creating embeddings for API documentation...")
        
        # Create a new collection for the embeddings
        self.collection = self.client.create_collection(
            name="alpha_vantage_docs",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Prepare the documents and metadata
        documents = []
        metadatas = []
        ids = []
        
        for i, endpoint in enumerate(endpoints):
            # Create a document that combines all the relevant information
            doc = f"""
            Function: {endpoint.function}
            Description: {endpoint.description}
            Required Parameters: {', '.join(endpoint.required_params.keys())}
            Optional Parameters: {', '.join(endpoint.optional_params.keys())}
            """
            
            # Create metadata that includes all the endpoint details
            metadata = {
                "name": endpoint.name,
                "description": endpoint.description,
                "function": endpoint.function,
                "endpoint": endpoint.endpoint,
                "required_params": json.dumps(endpoint.required_params),
                "optional_params": json.dumps(endpoint.optional_params)
            }
            if endpoint.example_response:
                metadata["example_response"] = endpoint.example_response
            
            documents.append(doc)
            metadatas.append(metadata)
            ids.append(str(i))
        
        # Add the documents to the collection
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info("Successfully created embeddings for API documentation")
    
    def query(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Query the API documentation using semantic search.
        
        Args:
            query: The search query
            top_k: Number of results to return
            
        Returns:
            List of dictionaries containing endpoint information
        """
        if not self.collection:
            raise ValueError("Documentation has not been embedded yet. Call embed_documentation() first.")
        
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        # Convert the results to a list of dictionaries
        endpoints = []
        for i, metadata in enumerate(results['metadatas'][0]):
            endpoint = {
                'name': metadata['name'],
                'description': metadata['description'],
                'function': metadata['function'],
                'endpoint': metadata['endpoint'],
                'required_params': json.loads(metadata['required_params']),
                'optional_params': json.loads(metadata['optional_params'])
            }
            if 'example_response' in metadata:
                endpoint['example_response'] = metadata['example_response']
            endpoints.append(endpoint)
        
        return endpoints
    
    def call_endpoint(self, function: str, **params) -> Dict:
        """Make an API call to Alpha Vantage
        
        Args:
            function: The API function to call (e.g., TIME_SERIES_DAILY)
            **params: Additional parameters for the API call
            
        Returns:
            API response as a dictionary
        """
        params["function"] = function
        params["apikey"] = self.api_key
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error calling Alpha Vantage API: {e}")
            raise 