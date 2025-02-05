import json
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import OllamaLLM

# Define a prompt template that instructs the LLM to extract intent and target
prompt_template = (
    "Extract the intent and target from the following query: '{query}'.\n"
    "Return your answer as a JSON object with keys 'intent' and 'target'."
)
template = PromptTemplate(input_variables=["query"], template=prompt_template)

llm = OllamaLLM(model = "deepseek-r1:7b")

# Create an LLMChain using the prompt template and the LLM
chain = template | llm | StrOutputParser()

def parse_user_query(query: str) -> dict:
    # Run the chain to get the response from the LLM
    response = chain.invoke(query)

    # Clean the response: attempt to strip any non-JSON prefix
    start = response.find('{')
    end = response.rfind('}')
    if start != -1 and end != -1 and end > start:
        json_str = response[start:end+1]
    else:
        # If no opening brace is found, log the raw response
        print("No JSON object found in response. Raw response:")
        json_str = response
    try:
        parsed = json.loads(json_str)
        return parsed
    except Exception as e:
        print("Error parsing response:", e)
        # Fallback heuristic: assume the last word is the target and the intent is 'sentiment'
        return {"intent": "sentiment", "target": query.split()[-1]}

if __name__ == "__main__":
    sample_query = "What is the sentiment towards Apple stock?"
    parsed_result = parse_user_query(sample_query)
    print("Parsed Result:", parsed_result)
