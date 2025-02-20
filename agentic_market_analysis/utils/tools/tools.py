from langchain_core.tools import tool

@tool
def call_alpha_vantage_api(url: str):
    """Make Alpha Vantage API call to the url"""
    ...

@tool
def generate_financial_report():
    """"""
    pass