from agentic_market_analysis.agents.researcher_agent import graph

input_message = "What is API endpoint for News Sentiment?"

for step in graph.stream(
    {"messages": [{"role": "user", "content": input_message}]},
    stream_mode="values",
):
    step["messages"][-1].pretty_print()