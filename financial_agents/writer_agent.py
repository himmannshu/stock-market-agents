from pydantic import BaseModel

from agents import Agent

# Updated prompt to incorporate news context
WRITER_PROMPT = (
    "You are a senior financial analyst. You will be provided with the original query, "
    "a set of raw web search summaries, and detailed financial data context about the company (including financials, metrics, segments, **news summaries**, filings, etc.). "
    "Your task is to synthesize ALL provided information into a cohesive, long‑form markdown report "
    "(at least several paragraphs) including a short executive summary and follow‑up questions. "
    "Integrate insights from the **news summary** and web searches to provide context on market sentiment, recent events, and outlook. "
    "The financial data provided contains valuable information about the company's financial performance, segments, "
    "and metrics that should be prominently incorporated into your analysis. "
    "If needed, you can call the available analysis tools (e.g. fundamentals_analysis, risk_analysis) "
    "to get short specialist write‑ups to incorporate."
)


class FinancialReportData(BaseModel):
    short_summary: str
    """A short 2‑3 sentence executive summary."""

    markdown_report: str
    """The full markdown report synthesizing all provided context."""

    follow_up_questions: list[str]
    """Suggested follow‑up questions for further research."""


# Note: We will attach handoffs to specialist analyst agents at runtime in the manager.
# This shows how an agent can use handoffs to delegate to specialized subagents.
writer_agent = Agent(
    name="FinancialWriterAgent",
    instructions=WRITER_PROMPT,
    model="gpt-4.5-preview-2025-02-27",
    output_type=FinancialReportData,
)
