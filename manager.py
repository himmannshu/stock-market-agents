from __future__ import annotations

import asyncio
import time
from collections.abc import Sequence

from rich.console import Console

from agents import Runner, RunResult, custom_span, gen_trace_id, trace

from financial_agents.financials_agent import financials_agent
from financial_agents.planner_agent import FinancialSearchItem, FinancialSearchPlan, planner_agent
from financial_agents.risk_agent import risk_agent
from financial_agents.search_agent import search_agent
from financial_agents.verifier_agent import VerificationResult, verifier_agent
from financial_agents.writer_agent import FinancialReportData, writer_agent
from financial_agents.financial_data_agent import financial_data_agent, FinancialDataAnalysis
from printer import Printer


async def _summary_extractor(run_result: RunResult) -> str:
    """Custom output extractor for sub‑agents that return an AnalysisSummary."""
    # The financial/risk analyst agents emit an AnalysisSummary with a `summary` field.
    # We want the tool call to return just that summary text so the writer can drop it inline.
    return str(run_result.final_output.summary)


class FinancialResearchManager:
    """
    Orchestrates the full flow: planning, searching, sub‑analysis, writing, and verification.
    """

    def __init__(self) -> None:
        self.console = Console()
        self.printer = Printer(self.console)

    async def run(self, query: str) -> None:
        trace_id = gen_trace_id()
        with trace("Financial research trace", trace_id=trace_id):
            self.printer.update_item(
                "trace_id",
                f"View trace: https://platform.openai.com/traces/{trace_id}",
                is_done=True,
                hide_checkmark=True,
            )
            self.printer.update_item("start", "Starting financial research...", is_done=True)
            
            # Extract company/ticker from query for financial data retrieval
            company_info = await self._extract_company_info(query)
            
            # Get financial data using the new agent
            financial_data = await self._get_financial_data(company_info)
            
            search_plan = await self._plan_searches(query)
            search_results = await self._perform_searches(search_plan)
            
            # Include financial data in report writing
            report = await self._write_report(query, search_results, financial_data)
            verification = await self._verify_report(report)

            final_report = f"Report summary\n\n{report.short_summary}"
            self.printer.update_item("final_report", final_report, is_done=True)

            self.printer.end()

        # Print to stdout
        print("\n\n=====REPORT=====\n\n")
        print(f"Report:\n{report.markdown_report}")
        print("\n\n=====FOLLOW UP QUESTIONS=====\n\n")
        print("\n".join(report.follow_up_questions))
        print("\n\n=====VERIFICATION=====\n\n")
        print(verification)

    async def _extract_company_info(self, query: str) -> str:
        """Extract company name or ticker from the query."""
        self.printer.update_item("extracting_company", "Identifying company/ticker from query...")
        
        # Use a simple approach to extract potential company or ticker from the query
        words = query.split()
        company_info = query
        
        self.printer.update_item(
            "extracting_company", 
            f"Identified company/ticker from query", 
            is_done=True
        )
        
        return company_info

    async def _get_financial_data(self, company_info: str) -> FinancialDataAnalysis:
        """Retrieve financial data using the financial data agent."""
        self.printer.update_item("financial_data", "Retrieving and analyzing financial data...")
        
        try:
            result = await Runner.run(financial_data_agent, f"Company/Ticker: {company_info}")
            financial_data = result.final_output_as(FinancialDataAnalysis)
            
            self.printer.update_item(
                "financial_data",
                f"Retrieved financial data for {financial_data.company_name} ({financial_data.ticker})",
                is_done=True,
            )
            
            return financial_data
        except Exception as e:
            self.printer.update_item(
                "financial_data",
                f"Error retrieving financial data: {str(e)}",
                is_done=True,
            )
            # Return an empty financial data object if retrieval fails
            return FinancialDataAnalysis(
                ticker="",
                company_name="",
                financial_summary="Failed to retrieve financial data.",
                key_metrics=[],
                growth_analysis="",
            )

    async def _plan_searches(self, query: str) -> FinancialSearchPlan:
        self.printer.update_item("planning", "Planning searches...")
        result = await Runner.run(planner_agent, f"Query: {query}")
        self.printer.update_item(
            "planning",
            f"Will perform {len(result.final_output.searches)} searches",
            is_done=True,
        )
        return result.final_output_as(FinancialSearchPlan)

    async def _perform_searches(self, search_plan: FinancialSearchPlan) -> Sequence[str]:
        with custom_span("Search the web"):
            self.printer.update_item("searching", "Searching...")
            tasks = [asyncio.create_task(self._search(item)) for item in search_plan.searches]
            results: list[str] = []
            num_completed = 0
            for task in asyncio.as_completed(tasks):
                result = await task
                if result is not None:
                    results.append(result)
                num_completed += 1
                self.printer.update_item(
                    "searching", f"Searching... {num_completed}/{len(tasks)} completed"
                )
            self.printer.mark_item_done("searching")
            return results

    async def _search(self, item: FinancialSearchItem) -> str | None:
        input_data = f"Search term: {item.query}\nReason: {item.reason}"
        try:
            result = await Runner.run(search_agent, input_data)
            return str(result.final_output)
        except Exception:
            return None

    async def _write_report(self, query: str, search_results: Sequence[str], financial_data: FinancialDataAnalysis) -> FinancialReportData:
        # Expose the specialist analysts as tools so the writer can invoke them inline
        # and still produce the final FinancialReportData output.
        fundamentals_tool = financials_agent.as_tool(
            tool_name="fundamentals_analysis",
            tool_description="Use to get a short write‑up of key financial metrics",
            custom_output_extractor=_summary_extractor,
        )
        risk_tool = risk_agent.as_tool(
            tool_name="risk_analysis",
            tool_description="Use to get a short write‑up of potential red flags",
            custom_output_extractor=_summary_extractor,
        )
        writer_with_tools = writer_agent.clone(tools=[fundamentals_tool, risk_tool])
        self.printer.update_item("writing", "Thinking about report...")
        
        # Format financial data string including the new segment analysis
        financial_data_str = (
            f"Financial Data Analysis for {financial_data.company_name} ({financial_data.ticker}):\n"
            f"Summary: {financial_data.financial_summary}\n"
            f"Key Metrics: {', '.join(financial_data.key_metrics)}\n"
            f"Growth Analysis: {financial_data.growth_analysis}\n"
            f"Revenue Segment Analysis: {financial_data.revenue_segment_analysis}\n"
        )
        if financial_data.risk_factors:
            financial_data_str += f"Risk Factors: {', '.join(financial_data.risk_factors)}\n"
        
        input_data = (
            f"Original query: {query}\n"
            f"Summarized web search results: {search_results}\n"
            f"Financial Data Context: \n{financial_data_str}"
        )
        
        result = Runner.run_streamed(writer_with_tools, input_data)
        update_messages = [
            "Planning report structure...",
            "Writing sections...",
            "Finalizing report...",
        ]
        last_update = time.time()
        next_message = 0
        async for _ in result.stream_events():
            if time.time() - last_update > 5 and next_message < len(update_messages):
                self.printer.update_item("writing", update_messages[next_message])
                next_message += 1
                last_update = time.time()
        self.printer.mark_item_done("writing")
        return result.final_output_as(FinancialReportData)

    async def _verify_report(self, report: FinancialReportData) -> VerificationResult:
        self.printer.update_item("verifying", "Verifying report...")
        result = await Runner.run(verifier_agent, report.markdown_report)
        self.printer.mark_item_done("verifying")
        return result.final_output_as(VerificationResult)
