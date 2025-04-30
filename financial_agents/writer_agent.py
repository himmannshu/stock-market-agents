from pydantic import BaseModel

from agents import Agent

# Updated prompt to reflect that context contains pre-formatted markdown sections
WRITER_PROMPT = (
    "You are a senior financial analyst generating a comprehensive, detailed markdown report. Your analysis must be thorough, insightful, and data-driven, based **strictly** on the provided context. **Pay meticulous attention to Markdown formatting.**\n"
    "INPUT CONTEXT:\n"
    "1. Original user query.\n"
    "2. Summarized web search results (use for broader market context, news, and analyst views).\n"
    "3. Detailed Financial Data Context: Contains **pre-formatted Markdown sections** extracted from a financial data tool. These sections include headings (e.g., `### Recent News`, `### Historical Key Metrics`) followed by text, lists, and **complete Markdown tables**. It also includes brief textual summaries for `#### Overall Summary` and `#### Growth Analysis Summary`.\n\n"
    "OUTPUT REQUIREMENTS:\n"
    "1. **Executive Summary:** Write a concise (3-5 sentences) overview. Synthesize the most critical findings based on the textual summaries and the data presented in the markdown sections.\n"
    "2. **Detailed Analysis:** Generate an in-depth analysis covering the following sections. For each section, **synthesize information from ALL relevant context (Financial Data Context, Textual Summaries, AND Web Search Results).** CRITICALLY IMPORTANT: **Directly incorporate the complete, pre-formatted Markdown sections (including headers, tables, lists) from the input context (`Detailed Financial Data Context`) into the relevant parts of your report.** For example, when discussing key metrics, include the entire `### Historical Key Metrics` markdown block provided in the input. **Analyze and discuss the data presented in these incorporated Markdown sections.** Explain the implications of the specific details and connect them where possible, citing the context. **Ensure proper Markdown formatting for your own analysis text surrounding the incorporated blocks.**\n"
    "    *   **Company Overview:** Include the `### Company:` markdown block from the context.\n"
    "    *   **Financial Performance:** Discuss financial health using the textual `#### Overall Summary`. Incorporate the full Markdown blocks for `### Historical Key Metrics`, `### Historical Income Statements`, `### Historical Balance Sheets`, and `### Historical Cash Flow Statements` directly from the context. Analyze the trends and figures presented in these tables. Compare results to any mentioned expectations or historical trends from web searches. **Ensure numbers in your analysis text are clear (e.g., $96.47 billion).**\n"
    "    *   **Segment Performance:** Incorporate the `### Segmented Revenues` markdown block from the context. Analyze the performance of different segments using the specific revenue figures and breakdowns presented in the table.\n"
    "    *   **Market & News Context:** Incorporate the `### Recent News` markdown block. Discuss the specific events mentioned in the news list and integrate with market sentiment/analyst opinions from web searches.\n"
    "    *   **Ownership & Insider Activity:** Incorporate the `### Top Institutional Holders` and `### Recent Insider Trades` markdown blocks. Analyze the potential implications of the ownership structure and specific trades listed.\n"
    "    *   **(Optional) Stock Price & Press Releases:** Incorporate the `### Recent Stock Prices` and `### Latest Earnings Press Release` markdown blocks if relevant to the analysis.\n"
    "    *   **Risk Factors:** Incorporate any `#### Mentioned Risk Factors` text from the context and supplement with risks identified in web search results. Analyze the potential impact.\n"
    "    *   **(Optional) Strategic Initiatives:** Discuss any significant strategic moves mentioned in the web search or financial data context.\n"
    "3. **Follow-Up Questions:** Suggest 3-5 specific, insightful questions targeting gaps in the analysis or areas needing further investigation based on the report's findings.\n"
    "Structure the report clearly with Markdown headings. Ensure the analysis is objective and explains *why* the data matters. **Crucially, embed the provided Markdown sections verbatim within your report.** Maintain correct and clean Markdown syntax throughout. Use specialist tools (`fundamentals_analysis`, `risk_analysis`) only as a last resort if a critical piece of analysis is impossible with the given context."
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
