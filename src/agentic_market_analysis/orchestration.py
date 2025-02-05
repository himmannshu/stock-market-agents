import pandas as pd
from agents import yahoo_finance_agent, sec_filings_agent

def orchestrate_data_collection(target: str) -> pd.DataFrame:
    """
    Aggregates data from the Yahoo Finance agent and the SEC Filings agent for the given target symbol.
    Returns a combined DataFrame with the columns: 'source', 'text', and 'sentiment'.
    """

    # Call the Yahoo Finance agent
    yahoo_df = yahoo_finance_agent(target)
    
    # Call the SEC Filings agent
    sec_df = sec_filings_agent(target)
    
    # Combine dataframes if at least one is non-empty
    if not yahoo_df.empty or not sec_df.empty:
        combined_df = pd.concat([yahoo_df, sec_df], ignore_index=True)
    else:
        combined_df = pd.DataFrame()
    
    return combined_df

if __name__ == "__main__":
    symbol = "AAPL"  # For testing
    combined_data = orchestrate_data_collection(symbol)
    print("Combined Data:")
    print(combined_data)
