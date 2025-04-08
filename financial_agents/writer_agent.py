from pydantic import BaseModel

from agents import Agent

# Writer agent brings together the raw search results and optionally calls out
# to sub‑analyst tools for specialized commentary, then returns a cohesive markdown report.
WRITER_PROMPT = (
    "You are a senior financial analyst. You will be provided with the original query, "
    "a set of raw search summaries, and detailed financial data about the company. "
    "Your task is to synthesize these into a long‑form markdown report (at least several paragraphs) "
    "including a short executive summary and follow‑up questions. "
    "The financial data provided contains valuable information about the company's financial performance "
    "and metrics that should be prominently incorporated into your analysis. "
    "If needed, you can call the available analysis tools (e.g. fundamentals_analysis, risk_analysis) "
    "to get short specialist write‑ups to incorporate."
)


class FinancialReportData(BaseModel):
    short_summary: str
    """A short 2‑3 sentence executive summary."""

    markdown_report: str
    """The full markdown report."""

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
