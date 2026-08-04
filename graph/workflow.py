from langgraph.graph import StateGraph, START, END

from states import AnalyzerState
from nodes import (
    summarize_ticket_node,
    retrieve_historical_context,
    generate_resolution_node,
    post_result_to_servicenow_node,
)
from utils.checkpointer import get_checkpointer

builder = StateGraph(AnalyzerState)

builder.add_node("summarize_ticket", summarize_ticket_node)
builder.add_node("retrieve_context", retrieve_historical_context)
builder.add_node("generate_solution", generate_resolution_node)
builder.add_node("post_to_servicenow", post_result_to_servicenow_node)

builder.add_edge(START, "summarize_ticket")
builder.add_edge("summarize_ticket", "retrieve_context")
builder.add_edge("retrieve_context", "generate_solution")
builder.add_edge("generate_solution", "post_to_servicenow")
builder.add_edge("post_to_servicenow", END)

checkpointer = get_checkpointer()
checkpointer.setup()  # idempotent: creates required tables if they don't exist

workflow = builder.compile(checkpointer=checkpointer)