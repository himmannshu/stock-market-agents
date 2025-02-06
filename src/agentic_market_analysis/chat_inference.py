import json
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import OllamaLLM

prompt_template = (
    "Given the following {query}, extract the intent, the target company name and its corresponding stock ticker symbol."
    "Return a valid JSON object with exactly three keys: ‘intent’, ‘target_company’, and ‘ticker’."
    "Guidelines:"
    "The ‘intent’ should reflect the nature of the query, such as ‘sentiment’."
    "The ‘target_company’ should be the full name of the company."
    "The ‘ticker’ should be the stock ticker symbol. If unsure, return an empty string for ‘ticker’."
    "Do not include any extra text or markdown. Return JSON object only."
    "Here are some examples to guide you:"
    "Example 1:"
    "Query: “What is the sentiment towards Apple stock?”"
    "Output: {{“intent”: “sentiment”, “target_company”: “Apple Inc.”, “ticker”: “AAPL”}}"
    "Example 2:"
    "Query: “How is Tesla’s stock performing today?”"
    "Output: {{“intent”: “performance”, “target_company”: “Tesla Inc.”, “ticker”: “TSLA”}}"
    "Example 3:"
    "Query: “Is Amazon a good investment currently?”"
    "Output: {{“intent”: “investment”, “target_company”: “Amazon.com Inc.”, “ticker”: “AMZN”}}"
)
template = PromptTemplate(input_variables=["query"], template=prompt_template)

llm = OllamaLLM(model="deepseek-r1:7b")
chain = template | llm | StrOutputParser()

def parse_user_query(query: str) -> dict:
    response = chain.invoke({"query": query})
    start = response.find('{')
    end = response.rfind('}')
    if start != -1 and end != -1 and end > start:
        json_str = response[start:end+1]
    else:
        print("No JSON object found in response. Raw response:", response)
        return {"intent": "sentiment", "target_company": query.split()[-1], "ticker": ""}
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print("Error parsing response:", e)
        return {"intent": "sentiment", "target_company": query.split()[-1], "ticker": ""}

if __name__ == "__main__":
    sample_query = "What is the sentiment towards Apple stock?"
    parsed_result = parse_user_query(sample_query)
    print("Parsed Result:", parsed_result)