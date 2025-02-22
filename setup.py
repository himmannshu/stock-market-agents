from setuptools import setup, find_packages

setup(
    name="agentic_market_analysis",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "langchain",
        "langchain-openai",
        "langgraph",
        "python-dotenv",
        # add other dependencies as needed
    ]
) 