import streamlit as st
import asyncio
import re
import pandas as pd
import io # For reading string as file

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

# --- Charting Helper Function ---
def extract_and_plot_charts(markdown_report):
    """Extracts CSV data from the markdown report and plots charts."""
    
    chart_data_block_match = re.search(r"<!-- CHART DATA START -->(.*?)<!-- CHART DATA END -->", markdown_report, re.DOTALL)
    
    if not chart_data_block_match:
        st.write("No chart data found in the report.")
        return
        
    chart_data_content = chart_data_block_match.group(1)
    
    # Find all CSV blocks within the chart data section
    csv_blocks = re.findall(r"```csv\n(#\s*(\w+)[\s\S]*?)\n```", chart_data_content)
    
    if not csv_blocks:
        st.write("No CSV data blocks found for charting.")
        return

    st.subheader("Visualizations")
    chart_count = 0
    for csv_content, chart_type in csv_blocks:
        try:
            # Use StringIO to treat the string CSV data as a file
            csv_file = io.StringIO(csv_content)
            df = pd.read_csv(csv_file, comment='#') # Use '#' as comment character
            
            if chart_type == "HISTORICAL_PRICES" and not df.empty:
                st.markdown("#### Historical Stock Prices (Close)")
                if 'Date' in df.columns and 'Close' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'])
                    df = df.set_index('Date')
                    st.line_chart(df['Close'])
                    chart_count += 1
                else:
                    st.warning(f"Could not plot {chart_type}: Missing 'Date' or 'Close' column.")
                    st.dataframe(df) # Show dataframe for debugging
                    
            elif chart_type == "HISTORICAL_METRICS" and not df.empty:
                st.markdown("#### Historical Metrics")
                if 'Year' in df.columns and 'Period' in df.columns:
                    # Combine Year and Period for a potential index, or just plot directly
                    # For simplicity, let's plot Market Cap if available
                    if 'MarketCap' in df.columns:
                         # Attempt to create a plottable index/column
                        df['ReportPeriod'] = df['Year'].astype(str) + '-' + df['Period']
                        # Basic plot, might need refinement based on actual data structure (annual/quarterly mix)
                        plot_df = df.set_index('ReportPeriod')
                        st.line_chart(plot_df['MarketCap'])
                        chart_count += 1
                    else:
                        st.warning(f"Could not plot {chart_type}: 'MarketCap' column not found.")
                        st.dataframe(df) # Show dataframe for debugging
                else:
                    st.warning(f"Could not plot {chart_type}: Missing 'Year' or 'Period' column.")
                    st.dataframe(df) # Show dataframe for debugging
            else:
                st.write(f"Unsupported or empty chart type found: {chart_type}")
                st.dataframe(df)

        except Exception as e:
            st.error(f"Failed to parse or plot chart data block ({chart_type}): {e}")
            st.text(csv_content) # Show raw block on error
            
    if chart_count == 0:
        st.write("No valid data found to plot charts.")

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
    # Clear previous report/charts
    report_placeholder.empty()
    
    analysis_results = run_manager(query)
    status_placeholder.empty()

    if analysis_results and analysis_results.get("markdown_report"):
        report_markdown = analysis_results["markdown_report"]
        
        # Display the main report (potentially excluding chart block if desired)
        # For now, display the full report including the raw data block
        report_placeholder.markdown(report_markdown)
        
        # Extract and plot charts from the report markdown
        extract_and_plot_charts(report_markdown)
        
        # Display follow-up questions and verification in expanders
        with st.expander("Follow-up Questions"):
            st.write(analysis_results.get("follow_up_questions", []))
        with st.expander("Verification Result"):
             st.write(analysis_results.get("verification_result", "Not available."))
             
    elif analysis_results:
        report_placeholder.warning("Report generation failed or returned empty.")
        
    
elif analyze_button and not query:
    st.warning("Please enter a company query.") 