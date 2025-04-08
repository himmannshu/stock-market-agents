import streamlit as st
import asyncio

from manager import FinancialResearchManager

# --- Streamlit Page Configuration ---
st.set_page_config(page_title="Financial Research Agent", layout="wide")

# --- UI Elements ---
st.title("Financial Research Agent 📈")

st.markdown("Enter a company name or ticker symbol below to generate a financial research report.")

query = st.text_input("Company Query:", placeholder="e.g., Analyze Apple's latest quarter", key="query_input")

analyze_button = st.button("Analyze", key="analyze_button")

# --- Report Display Area ---
report_placeholder = st.empty() # Placeholder for the final report
status_placeholder = st.empty() # Placeholder for status updates

# --- Backend Logic ---
def run_manager(user_query):
    """Instantiates and runs the FinancialResearchManager, returning the report."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        manager = FinancialResearchManager() # TODO: Pass status_placeholder for updates
        
        # Run the manager and get the results dictionary
        results = loop.run_until_complete(manager.run(user_query))
        
        # Return the results dictionary
        return results 

    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None # Indicate failure
    finally:
        loop.close()

# --- Button Click Handling ---
if analyze_button and query:
    status_placeholder.info("Processing your request... Please wait.") 
    # Clear previous report if any
    report_placeholder.empty()
    
    # Run the financial analysis and get results
    analysis_results = run_manager(query)
    
    # Clear status message
    status_placeholder.empty()

    # Display the report if results are available
    if analysis_results and analysis_results.get("markdown_report"):
        report_placeholder.markdown(analysis_results["markdown_report"])
        # Optionally display follow-up questions and verification
        with st.expander("Follow-up Questions"):
            st.write(analysis_results.get("follow_up_questions", []))
        with st.expander("Verification Result"):
             st.write(analysis_results.get("verification_result", "Not available."))
    elif analysis_results: # Handle case where run finished but report is missing
        report_placeholder.warning("Report generation failed or returned empty.")
    # Error case already handled by st.error inside run_manager
        
    
elif analyze_button and not query:
    st.warning("Please enter a company query.") 