from pydantic import BaseModel

from agents import Agent

# Updated prompt - trying different instruction order/wording for chart data
WRITER_PROMPT = (
    "You are a senior financial analyst generating a markdown report.\n"
    "INPUT CONTEXT:\n"
    "1. Original user query.\n"
    "2. Summarized web search results.\n"
    "3. Detailed Financial Data Context: Contains **textual summaries** (News, Trades, Ownership, Metrics, etc.) from the financial data agent.\n\n"
    "OUTPUT REQUIREMENTS:\n"
    "1. **Executive Summary** (2-3 sentences).\n"
    "2. **Detailed Analysis:** Analyze and synthesize the provided textual summaries and web search results. Discuss financial health, performance, sentiment, news, segments, insider trades, ownership, and filings. Correlate findings and highlight inconsistencies.\n"
    "3. **Follow-Up Questions:** Suggest relevant questions.\n"
    "Ensure your textual analysis is well-supported by the provided context. Use specialist tools (`fundamentals_analysis`, `risk_analysis`) sparingly only if essential."
)


class FinancialReportData(BaseModel):
    short_summary: str
    """A short 2‑3 sentence executive summary highlighting key synthesized findings."""

    markdown_report: str
    """The synthesized markdown report based on textual context."""

    follow_up_questions: list[str]
    """Suggested follow‑up questions for further research based on the synthesized analysis."""


# Note: We will attach handoffs to specialist analyst agents at runtime in the manager.
# This shows how an agent can use handoffs to delegate to specialized subagents.
writer_agent = Agent(
    name="FinancialWriterAgent",
    instructions=WRITER_PROMPT,
    model="gpt-4o", # Using GPT-4o as it might be better at following complex instructions like passing data verbatim
    output_type=FinancialReportData,
)
