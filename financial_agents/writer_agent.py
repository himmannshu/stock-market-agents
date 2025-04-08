from pydantic import BaseModel

from agents import Agent

# Updated prompt - trying different instruction order/wording for chart data
WRITER_PROMPT = (
    "You are a senior financial analyst generating a comprehensive, detailed markdown report. Your analysis must be thorough, insightful, and data-driven, based **strictly** on the provided context.\n"
    "INPUT CONTEXT:\n"
    "1. Original user query.\n"
    "2. Summarized web search results (use for broader market context, news, and analyst views).\n"
    "3. Detailed Financial Data Context: Contains **specific textual summaries and figures** (Financial Summary, News Summary, Insider Trades Summary, Institutional Ownership Summary, Key Metrics Summary, Growth Analysis, Revenue Segment Analysis, Risk Factors) extracted by a data agent.\n\n"
    "OUTPUT REQUIREMENTS:\n"
    "1. **Executive Summary:** Write a concise (3-5 sentences) overview. Synthesize the most critical findings regarding performance, key drivers, risks, and overall outlook based on the detailed analysis.\n"
    "2. **Detailed Analysis:** Generate an in-depth analysis covering the following sections. For each section, **synthesize information from ALL relevant context fields (Financial Data Context AND Web Search Results). CRITICALLY IMPORTANT: Include specific numbers, dates, growth rates, and figures provided in the context to support your analysis. Do not just state facts; explain their implications and connect them where possible.**\n"
    "    *   **Financial Performance:** Provide a detailed analysis of financial health. Discuss revenue, net income, EPS, and profitability, **using specific figures and growth rates** from the `Financial Summary`, `Key Metrics Summary`, and `Growth Analysis` fields. Compare results to any mentioned expectations or historical trends.\n"
    "    *   **Segment Performance:** Analyze the performance of different business/geographical segments **with specific revenue figures or growth percentages** from the `Revenue Segment Analysis` field. Discuss key drivers or challenges for each segment mentioned.\n"
    "    *   **Market & News Context:** Integrate recent news (`News Summary`), market sentiment (web searches), and analyst opinions (web searches). Discuss **specific events or announcements** and their potential impact. Quote specific analyst views if provided.\n"
    "    *   **Ownership & Insider Activity:** Discuss institutional ownership based on `Institutional Ownership Summary` and analyze the **specifics** of insider trades (`Insider Trades Summary`). Discuss potential implications of these activities. If data is explicitly stated as unavailable in context, acknowledge that.\n"
    "    *   **Risk Factors:** Detail the key risks identified in the `Risk Factors` field and web search results. Analyze the **potential impact** of these risks.\n"
    "    *   **(Optional) Strategic Initiatives:** Discuss any significant strategic moves, acquisitions, or investments mentioned in the context.\n"
    "3. **Follow-Up Questions:** Suggest 3-5 specific, insightful questions targeting gaps in the analysis or areas needing further investigation based on the report's findings.\n"
    "Structure the report clearly with Markdown headings. Ensure the analysis is objective, analytical (explaining *why* things matter), and rigorously supported by the specific details provided in the input context. Use specialist tools (`fundamentals_analysis`, `risk_analysis`) only as a last resort if a critical piece of analysis is impossible with the given context."
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
