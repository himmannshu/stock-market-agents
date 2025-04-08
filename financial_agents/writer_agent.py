from pydantic import BaseModel

from agents import Agent

# Updated prompt to emphasize synthesis and correlation
WRITER_PROMPT = (
    "You are a senior financial analyst tasked with creating a comprehensive and insightful report. "
    "You will be provided with:\n"
    "1. The original user query.\n"
    "2. Summarized web search results providing general context and recent events.\n"
    "3. Detailed Financial Data Context (from the financial_data_search tool) containing: News Summary, Insider Trades Summary, Institutional Ownership Summary, Key Metrics, Financial Statements, Segmented Revenues, SEC Filings info, etc.\n\n"
    "Your primary goal is to **synthesize** ALL this information into a cohesive, long-form markdown report (at least several paragraphs). Your report must include:\n"
    "- An **Executive Summary** (2-3 concise sentences).\n"
    "- A **Detailed Analysis** section. **Critically evaluate how the different data points relate to each other.** For example:\n"
    "    * Correlate recent news headlines and market sentiment (from web search/news summary) with stock price movements and reported financial performance.\n"
    "    * Analyze if insider trading activity aligns with or contradicts company news and performance trends.\n"
    "    * Discuss how segmented revenue performance and institutional ownership trends might reflect the company's strategic direction or market position.\n"
    "    * Identify any inconsistencies or contradictions between management statements (e.g., in press releases/filings, if available in context) and financial results or market news. Discuss potential reasons or implications.\n"
    "    * Integrate insights from SEC filings (like 8-Ks for major events or 10-Ks/Qs for detailed risks) when relevant to the analysis.\n"
    "- Suggested **Follow-Up Questions** for further research.\n\n"
    "Structure your report logically. Ensure your analysis is well-supported by the provided data context. "
    "You also have access to specialist tools (`fundamentals_analysis`, `risk_analysis`) if you need deeper dives into specific areas to enhance your synthesis, but prioritize using the provided context first."
)


class FinancialReportData(BaseModel):
    short_summary: str
    """A short 2‑3 sentence executive summary highlighting key synthesized findings."""

    markdown_report: str
    """The full markdown report synthesizing all provided context, including analysis of correlations and contradictions."""

    follow_up_questions: list[str]
    """Suggested follow‑up questions for further research based on the synthesized analysis."""


# Note: We will attach handoffs to specialist analyst agents at runtime in the manager.
# This shows how an agent can use handoffs to delegate to specialized subagents.
writer_agent = Agent(
    name="FinancialWriterAgent",
    instructions=WRITER_PROMPT,
    model="gpt-4.5-preview-2025-02-27", # Consider GPT-4o for potentially better synthesis
    output_type=FinancialReportData,
)
