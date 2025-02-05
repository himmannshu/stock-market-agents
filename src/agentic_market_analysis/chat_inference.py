import json
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import OllamaLLM

prompt_template = (
    "Given the following query: {query}, extract the intent, the target company name and its corresponding stock ticker symbol. "
    "Return a valid JSON object with exactly three keys: 'intent', 'target_company' and 'ticker'. "
    "For example, if the query is 'What is the sentiment towards Apple stock?', the output should be: "
    '{{"intent": "sentiment", "target_company": "Apple Inc.", "ticker": "AAPL"}}. '
    "If you are not sure about the ticker symbol, return an empty string for 'ticker'. "
    "Do not include any extra text or markdown."
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