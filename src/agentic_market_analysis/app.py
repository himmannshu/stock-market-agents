import streamlit as st
import pandas as pd
import plotly.express as px

from chat_inference import parse_user_query
from orchestration import orchestrate_data_collection

# Set the page configuration
st.set_page_config(page_title="Stock Sentiment Analysis Interface", layout="wide")

# Sidebar Navigation
st.sidebar.header("Navigation")
nav_option = st.sidebar.selectbox("Go to", ["Home", "Sentiment Analysis", "Visualizations"])

if nav_option == "Home":
    st.title("Stock Sentiment Analysis Interface")
    st.markdown("""
    Welcome! This tool aggregates data from multiple sources to provide a comprehensive sentiment analysis on stocks.
    Enter a query such as *"What is the sentiment towards Apple stock?"* to get started.
    """)

elif nav_option == "Sentiment Analysis":
    st.title("Sentiment Analysis")
    user_query = st.text_input("Enter your query:", value="What is the sentiment towards Apple stock?")
    
    if st.button("Analyze Query"):
        # Parse the user query using our chat_inference module
        parsed_result = parse_user_query(user_query)
        st.subheader("Parsed Query")
        st.json(parsed_result)
        
        target = parsed_result.get("target", "")
        if target:
            st.write(f"Aggregating data for target: **{target}**")
            with st.spinner("Collecting data from Yahoo Finance and SEC Filings..."):
                combined_df = orchestrate_data_collection(target)
            if combined_df.empty:
                st.error("No data found for the specified target.")
            else:
                st.subheader("Aggregated Data")
                st.dataframe(combined_df)
                
                # Visualization: Sentiment Distribution (assuming each sentiment is a dict with key 'label')
                st.subheader("Sentiment Distribution")
                # Extract the sentiment label for each row
                combined_df["Sentiment Label"] = combined_df["sentiment"].apply(lambda x: x.get("label", "NEUTRAL"))
                sentiment_counts = combined_df["Sentiment Label"].value_counts().reset_index()
                sentiment_counts.columns = ["Sentiment", "Count"]
                fig = px.bar(sentiment_counts, x="Sentiment", y="Count", title="Sentiment Distribution")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Could not extract a target from your query. Please try rephrasing.")

elif nav_option == "Visualizations":
    st.title("Advanced Visualizations")
    st.markdown("More advanced charts and interactive visualizations will be added here.")
    # Further visualization code can be added as your project evolves.
