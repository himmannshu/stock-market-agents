# Financial Research Agent Example

This example shows how you might compose a richer financial research agent using the Agents SDK. The pattern is similar to the `research_bot` example, but with more specialized sub‑agents and a verification step.

The flow is:

1. **Planning**: A planner agent turns the end user's request into a list of search terms relevant to financial analysis – recent news, earnings calls, corporate filings, industry commentary, etc.
2. **Financial Data**: A financial data agent retrieves detailed financial information for the company using the Financial Datasets API, including income statements, balance sheets, and key metrics.
3. **Search**: A search agent uses the built‑in `WebSearchTool` to retrieve terse summaries for each search term. (You could also add `FileSearchTool` if you have indexed PDFs or 10‑Ks.)
4. **Sub‑analysts**: Additional agents (e.g. a fundamentals analyst and a risk analyst) are exposed as tools so the writer can call them inline and incorporate their outputs.
5. **Writing**: A senior writer agent brings together the search snippets, financial data, and any sub‑analyst summaries into a long‑form markdown report plus a short executive summary.
6. **Verification**: A final verifier agent audits the report for obvious inconsistencies or missing sourcing.

You can run the example with:

```bash
python -m examples.financial_research_agent.main
```

and enter a query like:

```
Write up an analysis of Apple Inc.'s most recent quarter.
```

### Starter prompt

The writer agent is seeded with instructions similar to:

```
You are a senior financial analyst. You will be provided with the original query,
a set of raw search summaries, and detailed financial data about the company.
Your task is to synthesize these into a long‑form markdown report (at least several paragraphs)
with a short executive summary. You also have access to tools like `fundamentals_analysis` and
`risk_analysis` to get short specialist write‑ups if you want to incorporate them.
The financial data provided contains valuable information about the company's financial performance
and metrics that should be prominently incorporated into your analysis.
Add a few follow‑up questions for further research.
```

### Financial Datasets API

The system now leverages the [Financial Datasets API](https://docs.financialdatasets.ai/introduction) to retrieve comprehensive financial information about companies, including:

- Income statements
- Balance sheets
- Cash flow statements
- Financial metrics
- Stock prices
- Company information

To use this functionality, you'll need to:

1. Sign up for an API key at [financialdatasets.ai](https://financialdatasets.ai)
2. Add your API key to the `.env` file as `FINANCIAL_DATASETS_API_KEY=your_key_here`

You can tweak these prompts and sub‑agents to suit your own data sources and preferred report structure.
