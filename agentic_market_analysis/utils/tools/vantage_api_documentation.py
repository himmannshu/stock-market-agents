import requests
from bs4 import BeautifulSoup
import json

def scrape_alpha_vantage_api_docs(documentation_url):
    response = requests.get(documentation_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    api_endpoint_rules = []
    endpoint_headings = soup.find_all('h4')

    for heading_tag in endpoint_headings:
        endpoint_name_element = heading_tag.find('a') # Try to find <a> tag INSIDE <h4>
        if endpoint_name_element: # Case 1: <a> tag exists
            full_endpoint_header = endpoint_name_element.text.strip()
            endpoint_name = full_endpoint_header.replace("Trending", "").replace("Premium", "").strip()
        else: # Case 2: No <a> tag, name is directly in <h4>
            full_endpoint_header = heading_tag.text.strip()
            endpoint_name = full_endpoint_header.replace("Trending", "").replace("Premium", "").strip()
            
        api_url_path = f"/query?function={endpoint_name}"

        api_url_path = f"/query?function={endpoint_name}"
        description = ""
        parameters = []
        example_request_urls = []
        is_premium = "Premium" in full_endpoint_header
        is_trending = "Trending" in full_endpoint_header

        description_tag = heading_tag.find_next_sibling('p')
        if description_tag:
            description = description_tag.text.strip()

        params_heading = None
        current_element = heading_tag.find_next_sibling()
        while current_element and current_element.name not in ['h4', 'h5', 'section', 'div', 'article']: # Stop at next major section break, not just <h6>
            if current_element.name == 'h6' and "API Parameters" in current_element.text: # Check if <h6> and text *contains* "API Parameters"
                params_heading = current_element
                break
            current_element = current_element.find_next_sibling()
 
        if params_heading:
            # --- ISOLATE API PARAMETERS SECTION ---
            params_section_end_tag = params_heading.find_next_sibling('h6') # Look for next <h6> to mark section end
            if not params_section_end_tag: # If no next <h6>, assume section ends at the end of container
                params_section_end_tag = heading_tag.find_parent(['section', 'article']) # Or adjust container tag if needed
            parameter_p_tags = []
            current_element = params_heading.find_next_sibling()
            
            while current_element and current_element != params_section_end_tag: # Iterate within the parameters section
                if current_element.name == 'p':
                    parameter_p_tags.append(current_element)
                current_element = current_element.find_next_sibling()
                # DEBUG PARAM SECTION: Found parameter <p> tags in section
            
            param_element_iterator = iter(parameter_p_tags) # Create an iterator
            param_element = next(param_element_iterator, None) # Get the first parameter <p> tag or None
            
            while param_element: # Loop through parameter <p> tags
                if param_element and param_element.name == 'p' and '❚' in param_element.text and ("Required:" in param_element.text or "Optional:" in param_element.text):
                    param_text = param_element.text.strip()
                    required_match = "❚ Required:" in param_text
                    #optional_match = "❚ Optional:" in param_text
                    required = required_match
                    param_name_code = param_element.find('code')
                    param_name = param_name_code.text.strip() if param_name_code else "N/A"
                    # --- DESCRIPTION EXTRACTION - LOOK FOR <p> TAGS IMMEDIATELY FOLLOWING PARAMETER DEFINITION ---
                    desc_element = param_element.find_next_sibling('p')
                    param_description = desc_element.text.strip()
                    # Later "allowed_values": None # Allowed values - later
                    parameters.append({
                        "name": param_name,
                        "type": "string",
                        "required": required,
                        "description": param_description # Description extraction - needs refinement
                    })
                # --- ADVANCE TO NEXT PARAMETER <p> TAG WITHIN SECTION ---
                param_element = next(param_element_iterator, None) # Get the next parameter <p> tag from iterator
        # ... (rest of the code) ...
        example_heading = None
        
        while current_element and current_element.name not in ['h4', 'h5', 'section', 'div', 'article']:
            if current_element.name == 'h6' and 'Examples' in current_element.text:
                example_heading = current_element
                break
            current_element = current_element.find_next_sibling()

        if example_heading:
            example_p_tags = []
            p_element = example_heading.find_next_sibling('p')
            while p_element and p_element.name == 'p' and 'alphavantage.co/query' in p_element.decode_contents():
                example_p_tags.append(p_element)
                p_element = p_element.find_next_sibling('p')

            for p_tag in example_p_tags:
                url_code_tag = p_tag.find('code')
                if url_code_tag:
                    example_url = url_code_tag.text.strip()
                    if 'csv' not in example_url.lower():
                        example_request_urls.append(example_url)
        
        api_endpoint_rules.append({
            "endpoint_name": endpoint_name,
            "api_url_path": api_url_path,
            "description": description,
            "parameters": parameters,
            "example_request_url": example_request_urls[0] if example_request_urls else "N/A",
            "output_fields": [],
            "is_premium": is_premium,
            "is_trending": is_trending
        })

    return api_endpoint_rules


if __name__ == "__main__":
    documentation_url = "https://www.alphavantage.co/documentation/"
    api_rules = scrape_alpha_vantage_api_docs(documentation_url)

    with open("alpha_vantage_api_rules.json", 'w') as outfile:
        json.dump(api_rules, outfile, indent=2)

    print("API rules JSON file created: alpha_vantage_api_rules.json")
    print(f"Extracted {len(api_rules)} endpoint rules.")