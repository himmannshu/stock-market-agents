"""Tool for interacting with Alpha Vantage API"""
import os
import json
import requests
from bs4 import BeautifulSoup
import chromadb
from chromadb.config import Settings
from chromadb.errors import InvalidCollectionException
from typing import Dict, List, Optional, Union, Tuple, Any
from dataclasses import dataclass
import logging
import re
from ..config.database import CHROMA_SETTINGS
from ..utils.cache import Cache

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
        self.collection_name = collection_name
        self.cache = Cache("alpha_vantage")  # Initialize cache first
        
        logger.info(f"Initializing ChromaDB with persist_directory: {CHROMA_SETTINGS['persist_directory']}")
        
        try:
            # Initialize ChromaDB with persistent storage
            logger.info("Creating ChromaDB client...")
            self.client = chromadb.PersistentClient(
                path=CHROMA_SETTINGS["persist_directory"]
            )
            logger.info("ChromaDB client created successfully")
            
            # Try to get existing collection or create new one
            try:
                logger.info(f"Attempting to get collection '{collection_name}'...")
                self.collection = self.client.get_collection(name=collection_name)
                count = self.collection.count()
                logger.info(f"Found existing collection '{collection_name}' with {count} documents")
            except (ValueError, InvalidCollectionException):
                logger.info(f"Collection not found. Creating new collection '{collection_name}'...")
                self.collection = self.client.create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info("Collection created successfully")
            
            # Initialize embeddings if collection is empty
            count = self.collection.count()
            logger.info(f"Checking collection count: {count}")
            if count == 0:
                logger.info("No endpoints found in database. Starting documentation scraping...")
                endpoints = self.scrape_documentation()
                logger.info(f"Documentation scraped successfully. Found {len(endpoints)} endpoints")
                logger.info("Creating embeddings...")
                self.embed_documentation(endpoints)
                logger.info("Embeddings created successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {str(e)}", exc_info=True)
            raise
    
    def _get_cache_key(self, function: str, params: Dict[str, Any]) -> str:
        """Generate a cache key for an API call
        
        Args:
            function: API function name
            params: API parameters
            
        Returns:
            Cache key string
        """
        # Sort parameters to ensure consistent cache keys
        sorted_params = dict(sorted(params.items()))
        return f"{function}:{json.dumps(sorted_params)}"
    
    def make_api_call(self, function: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make an API call to Alpha Vantage with caching
        
        Args:
            function: API function to call
            params: Parameters for the API call
            
        Returns:
            API response data
        """
        # Add function to params for the actual API call
        api_params = params.copy()
        api_params["function"] = function
        api_params["apikey"] = self.api_key
        
        cache_key = self._get_cache_key(function, params)
        
        # Try to get from cache first
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            logger.info(f"Cache hit for {function}")
            return cached_result
        
        # Make API call if not in cache
        try:
            response = requests.get(self.base_url, params=api_params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Cache the result
            # Use a longer expiry for historical data that doesn't change often
            if any(k in function.upper() for k in ["DAILY", "WEEKLY", "MONTHLY", "EARNINGS", "OVERVIEW"]):
                expiry = 24 * 3600  # 24 hours for historical data
            else:
                expiry = 300  # 5 minutes for real-time data
            
            self.cache.set(cache_key, data, expiry)
            return data
            
        except requests.RequestException as e:
            logger.error(f"API call failed: {str(e)}")
            raise
    
    def query_endpoints(self, question: str, top_k: int = 5) -> List[APIEndpoint]:
        """Query the embeddings database for relevant endpoints
        
        Args:
            question: The question to find relevant endpoints for
            top_k: Number of results to return
            
        Returns:
            List of relevant API endpoints
        """
        results = self.collection.query(
            query_texts=[question],
            n_results=top_k
        )
        
        endpoints = []
        for idx, metadata in enumerate(results["metadatas"][0]):
            endpoint = APIEndpoint(
                name=metadata["name"],
                description=metadata["description"],
                endpoint=metadata["endpoint"],
                function=metadata["function"],
                required_params=json.loads(metadata["required_params"]),
                optional_params=json.loads(metadata["optional_params"]),
                example_response=metadata.get("example_response")
            )
            endpoints.append(endpoint)
        
        return endpoints
    
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
            
        Returns:
            List of API endpoints
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
                # Skip if this is not an API endpoint
                header_text = endpoint_header.get_text(strip=True)
                if not header_text or "API Parameters" in header_text or "Examples" in header_text:
                    continue
                
                # Get the description (next p tag)
                description = ""
                next_elem = endpoint_header.find_next_sibling()
                while next_elem and next_elem.name == "p":
                    description += " " + next_elem.get_text(strip=True)
                    next_elem = next_elem.find_next_sibling()
                
                # Find the parameters table
                params_table = None
                current = endpoint_header
                while current and not params_table:
                    current = current.find_next_sibling()
                    if current and current.name == "table":
                        params_table = current
                
                # Extract parameters from table
                required_params = {}
                optional_params = {}
                if params_table:
                    for row in params_table.find_all("tr")[1:]:  # Skip header row
                        cols = row.find_all("td")
                        if len(cols) >= 2:
                            param_name = cols[0].get_text(strip=True)
                            param_desc = self._clean_description(cols[1].get_text())
                            
                            # Check if parameter is required (contains "required" in description)
                            if "required" in param_desc.lower():
                                required_params[param_name] = param_desc
                            else:
                                optional_params[param_name] = param_desc
                
                # Find example response
                example_response = None
                example_header = None
                current = params_table if params_table else endpoint_header
                while current:
                    current = current.find_next_sibling()
                    if current and current.name == "h5" and "Example" in current.get_text():
                        example_header = current
                        break
                
                if example_header:
                    example_pre = example_header.find_next_sibling("pre")
                    if example_pre:
                        example_response = example_pre.get_text(strip=True)
                
                # Extract function name from the API endpoint
                function_name = header_text.split("(")[0].strip()
                
                # Create endpoint object
                endpoint = APIEndpoint(
                    name=header_text,
                    description=description.strip(),
                    endpoint=self.base_url,
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
    
    def call_endpoint(self, function: str, **params) -> Dict[str, Any]:
        """Make an API call to Alpha Vantage
        
        Args:
            function: The API function to call (e.g., TIME_SERIES_DAILY)
            **params: Additional parameters for the API call
            
        Returns:
            API response as a dictionary
        """
        return self.make_api_call(function, params)