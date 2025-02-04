from langchain_ollama import OllamaLLM
from langchain_ollama import ChatOllama


llm = OllamaLLM(model = "aratan/deepseek-r1-32b")
chat_model = ChatOllama(model = "aratan/deepseek-r1-32b")

for chunk in llm.stream("tell me a joke"):
    print(chunk, end="|", flush=True)


import yfinance as yf
stock = yf.Ticker("TSLA")
news = stock.news  # Fetches recent news headlines

print(news)