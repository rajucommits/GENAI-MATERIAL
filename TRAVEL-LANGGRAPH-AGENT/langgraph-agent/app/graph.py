from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.state import TravelState
from app.nodes import *

def route(state: TravelState):
    # Safe check using .get() to prevent crashes if the node hasn't run
    if state.get("remaining_budget", 0) < 0: 
        return "warn"
    return "proceed"

builder = StateGraph(TravelState)

# 1. ADD A REVIEW NODE
builder.add_node("processor", input_processor_node)
builder.add_node("flights", flight_agent)
builder.add_node("hotels", hotel_agent)
builder.add_node("budget_check", budget_check_node)
builder.add_node("supervisor", supervisor_node)
builder.add_node("budget_warning", budget_warning_node)
builder.add_node("activities", activity_agent)
builder.add_node("review_itinerary", lambda state: state) # 👈 Just a placeholder
builder.add_node("booking_node", booking_node)

# 2. UPDATE THE EDGES
builder.set_entry_point("processor")
builder.add_edge("processor", "flights")
builder.add_edge("flights", "hotels")
builder.add_edge("hotels", "budget_check") 
builder.add_edge("budget_check", "supervisor")

builder.add_conditional_edges(
    "supervisor", 
    route, 
    {"warn": "budget_warning", "proceed": "activities"}
)

# 👈 Change: Activities go to REVIEW, not BOOKING
builder.add_edge("activities", "review_itinerary") 
builder.add_edge("review_itinerary", "booking_node") 

builder.add_edge("budget_warning", END)
builder.add_edge("booking_node", END)

# 3. UPDATE THE INTERRUPT
memory = MemorySaver()
graph = builder.compile(
    checkpointer=memory, 
    interrupt_before=["booking_node"] # 🚨 The graph stops HERE. 
)