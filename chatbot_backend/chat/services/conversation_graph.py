from langgraph.graph import StateGraph, END

from chat.services.langgraph_state import ConversationState
from chat.services.langgraph_nodes.stage_analyzer import analyze_stage_node
from chat.services.langgraph_nodes.response_generator import generate_response_node
from chat.services.langgraph_nodes.lead_extractor import extract_lead_node


def should_extract_lead(state: ConversationState) -> str:
    """
    Conditional router for lead extraction.
    """
    return "extract" if state.should_extract_lead else "skip"


def build_conversation_graph():
    graph = StateGraph(ConversationState)

    # ---- Register nodes ----
    graph.add_node("stage_analyzer", analyze_stage_node)
    graph.add_node("response_generator", generate_response_node)
    graph.add_node("lead_extractor", extract_lead_node)

    # ---- Define flow ----
    graph.set_entry_point("stage_analyzer")

    graph.add_edge("stage_analyzer", "response_generator")

    graph.add_conditional_edges(
        "response_generator",
        should_extract_lead,
        {
            "extract": "lead_extractor",
            "skip": END
        }
    )

    graph.add_edge("lead_extractor", END)

    return graph.compile()
