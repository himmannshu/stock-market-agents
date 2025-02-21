from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from agentic_market_analysis.utils.tools.tools import call_alpha_vantage_api
from dotenv import load_dotenv

llm = ChatOpenAI(model='gpt-4o')

researcher_agent = create_react_agent(llm, tools=[call_alpha_vantage_api])


from langchain_core.prompts import PromptTemplate

template = """Use the following pieces of context to answer the question at the end.
If you don't know the answer, just say that you don't know, don't try to make up an answer.
Provide the answer in the following json format with following keys: url_endpoint, required_arguments, optional_arguments, allowed_values and description.
allowed_values and description will be children of required_arguments and optional_arguments key in the json object.
Do not make up any arguments.
{context}

Question: {question}

Helpful Answer:"""

custom_rag_prompt = PromptTemplate.from_template(template)


def generate(q):
    docs_content = "\n\n".join(doc.page_content for doc in q["context"])
    messages = custom_rag_prompt.invoke({"question": q["question"], "context": docs_content})
    response = llm.invoke(messages)
    return {"answer": response.content}

