import streamlit as st
import asyncio
import re

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

# --- Initialize session state --- 
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None

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
    # Clear previous results from session state and placeholders for a new analysis
    report_placeholder.empty()
    st.session_state.analysis_results = None
    
    # Run analysis and store results in session state
    st.session_state.analysis_results = run_manager(query)
    status_placeholder.empty()

    # Display immediately after generation
    if st.session_state.analysis_results and st.session_state.analysis_results.get("markdown_report"):
        pass # Handled by the display block below
    elif st.session_state.analysis_results:
        report_placeholder.warning("Report generation failed or returned empty.")

elif analyze_button and not query:
    st.warning("Please enter a company query.") 

# --- Display Results (if available in session state) --- 
if st.session_state.analysis_results and st.session_state.analysis_results.get("markdown_report"):
    report_markdown = st.session_state.analysis_results["markdown_report"]
    
    # Use the stored query if available, otherwise fallback
    current_query = st.session_state.get('query_input', query or "report") 
    
    # Download button 
    if current_query:
        filename_query_part = re.sub(r'\W+', '_', current_query)
        filename = f"financial_report_{filename_query_part[:30]}.md" # Limit length
        st.download_button(
            label="Download Report (Markdown)",
            data=report_markdown,
            file_name=filename,
            mime="text/markdown",
        )

    # Display report using placeholder
    report_placeholder.markdown(report_markdown)
    
    # Display expanders
    with st.expander("Follow-up Questions"):
        st.write(st.session_state.analysis_results.get("follow_up_questions", []))
    with st.expander("Verification Result"):
        st.write(st.session_state.analysis_results.get("verification_result", "Not available.")) 