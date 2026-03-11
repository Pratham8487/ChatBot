"""
Pydantic schemas for the LangChain agent.

WHY: Replaces the ad-hoc dict-based data passing with typed, validated models.
     LangChain tools use these as return types for structured output.
     The agent parses tool results into these schemas automatically.

WHERE USED:
  - agent_tools.py: Tools return these schemas
  - langchain_agent.py: Agent result is parsed into AgentResponse
  - views.py: Consumes AgentResponse to build the API JSON response
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal


class StageDecision(BaseModel):
    """
    Returned by the detect_stage tool.

    The agent calls detect_stage after reading the user's message to decide
    whether the conversation should advance to the next funnel stage.

    Fields:
      - current_stage: Where the conversation is right now
      - next_stage: Where it should move to (may be the same if not ready)
      - reasoning: Why the agent decided to advance or stay
    """
    current_stage: str = Field(description="The stage before this turn")
    next_stage: str = Field(description="The stage after this turn")
    reasoning: str = Field(description="Brief explanation of why the stage changed or stayed")


class LeadInfo(BaseModel):
    """
    Structured lead data extracted from conversation.

    Replaces the old LeadData dataclass + _safe_json_extract() approach.
    The agent calls extract_lead_info tool which returns this schema,
    so we get validated, typed data instead of raw JSON parsing.

    Fields mirror the Lead Django model for easy persistence.
    """
    name: Optional[str] = Field(default=None, description="Visitor's name")
    email: Optional[str] = Field(default=None, description="Visitor's email address")
    phone: Optional[str] = Field(default=None, description="Visitor's phone number")
    company: Optional[str] = Field(default=None, description="Visitor's company name")
    problem: Optional[str] = Field(default=None, description="Business problem described by visitor")
    intent_level: Literal["low", "medium", "high"] = Field(
        default="low",
        description="Inferred purchase intent: low (browsing), medium (interested), high (ready to buy)"
    )

    def is_qualified(self) -> bool:
        """
        Business rule: a lead is qualified when intent is high
        AND at least one contact method (email or phone) is provided.
        Mirrors the old LeadData.is_qualified() logic.
        """
        return self.intent_level == "high" and bool(self.email or self.phone)


class AgentResponse(BaseModel):
    """
    The final structured output from invoke_agent().

    This is what the view layer consumes. It bundles together:
      - The chatbot's text response to the user
      - The conversation stage after this turn
      - Extracted lead information (if any)

    WHY a single response object: The old code made 2 separate LLM calls
    (one for response, one for lead extraction). The agent does both in
    a single invocation by calling tools, so we package all results together.
    """
    stage: str = Field(description="Conversation stage after this turn")
    response: str = Field(description="The chatbot's reply to the user")
    lead: LeadInfo = Field(default_factory=LeadInfo, description="Extracted lead data")
