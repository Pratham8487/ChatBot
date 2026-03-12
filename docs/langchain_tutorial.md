# LangChain Complete Tutorial

*A mentor's guide from beginner to production AI systems*

## Table of Contents
- [Chapter 1 — What is LangChain](#chapter-1--what-is-langchain)
- [Chapter 2 — LLM Basics](#chapter-2--llm-basics)
- [Chapter 3 — Prompt Templates](#chapter-3--prompt-templates)
- [Chapter 4 — Chains](#chapter-4--chains)
- [Chapter 5 — Agents](#chapter-5--agents)
- [Chapter 6 — Tools](#chapter-6--tools)
- [Chapter 7 — Memory](#chapter-7--memory)
- [Chapter 8 — Retrieval Augmented Generation (RAG)](#chapter-8--retrieval-augmented-generation-rag)
- [Chapter 9 — Production AI Systems](#chapter-9--production-ai-systems)
- [Chapter 10 — Building a Full AI Chatbot](#chapter-10--building-a-full-ai-chatbot)

---

## Chapter 1 — What is LangChain

### What Problem Does LangChain Solve?

Imagine you want to build an AI application. You could call the OpenAI API directly:

```python
from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}]
)
```

This works for simple cases. But real applications need:
- **Conversation history** (memory across turns)
- **External data access** (databases, APIs, documents)
- **Decision-making** (which tool to use, when to stop)
- **Structured output** (JSON, not just text)
- **Multiple LLM providers** (swap OpenAI for Ollama without rewriting)

LangChain provides **building blocks** for all of these. It's a framework that sits between your application code and the LLM, handling the complex orchestration.

### The LangChain Ecosystem

```
┌─────────────────────────────────────────────┐
│           Your Application Code              │
├─────────────────────────────────────────────┤
│  LangChain                                   │
│  ├── langchain-core    (base abstractions)   │
│  ├── langchain         (chains, agents)      │
│  ├── langchain-openai  (OpenAI integration)  │
│  ├── langchain-ollama  (Ollama integration)  │
│  └── langgraph         (agent orchestration) │
├─────────────────────────────────────────────┤
│  LLM Providers                               │
│  ├── OpenAI API                              │
│  ├── Ollama (local)                          │
│  ├── Anthropic                               │
│  └── ... 50+ providers                       │
└─────────────────────────────────────────────┘
```

### Key Concepts

| Concept | What It Is | Analogy |
|---------|-----------|---------|
| **LLM** | The AI model that generates text | The brain |
| **Prompt** | Instructions sent to the LLM | The question you ask |
| **Chain** | A sequence of steps executed in order | A recipe |
| **Agent** | An LLM that can decide which tools to use | A worker who chooses their own tools |
| **Tool** | A function the agent can call | A specific ability (search, calculate, etc.) |
| **Memory** | State persisted across interactions | Short-term and long-term memory |
| **Retriever** | Fetches relevant documents from a data source | A librarian finding the right books |

### How This Project Uses LangChain

This chatbot project uses LangChain in a specific way:

```
User Message → LangChain ReAct Agent → Tool Calls → LLM Response
                     ↕                      ↕
              LangGraph State         PostgreSQL DB
```

The agent uses **4 custom tools** to manage a sales funnel conversation, and **LangGraph** to maintain state across HTTP requests.

### Practice Task

> **Task**: Install LangChain and verify your setup.
> ```bash
> pip install langchain langchain-core langchain-openai langgraph
> ```
> Then run:
> ```python
> import langchain
> print(langchain.__version__)
> ```
> Verify the version is 0.3.x or later.

---

## Chapter 2 — LLM Basics

### What is an LLM?

A Large Language Model (LLM) is a neural network trained on vast amounts of text. You send it a prompt (text input), and it generates a response (text output). Think of it as a very sophisticated autocomplete.

### Using LLMs with LangChain

LangChain wraps LLMs in a unified interface. This means you can swap providers without changing your application code.

#### OpenAI

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4o",
    api_key="sk-your-key",
    temperature=0.3,        # 0 = deterministic, 1 = creative
)

response = llm.invoke("What is solar energy?")
print(response.content)
```

#### Ollama (Local)

```python
from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="llama3",
    base_url="http://localhost:11434",
    temperature=0.3,
)

response = llm.invoke("What is solar energy?")
print(response.content)
```

#### LM Studio (OpenAI-compatible local)

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="local-model",
    base_url="http://localhost:1234/v1",
    api_key="lm-studio",     # LM Studio doesn't need a real key
    temperature=0.3,
)
```

### How This Project Chooses an LLM

From `langchain_agent.py`:

```python
def get_llm(engine: str):
    if engine == "openai":
        return ChatOpenAI(model="gpt-4o", api_key=settings.OPENAI_API_KEY)
    elif engine == "ollama":
        return ChatOllama(model="llama3", base_url="http://localhost:11434")
    elif engine == "lmstudio":
        return ChatOpenAI(model="local-model", base_url="http://localhost:1234/v1")
```

The `engine` parameter comes from the API query string: `/api/chat/?engine=openai`

### Message Types

LangChain uses typed messages instead of raw strings:

```python
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

messages = [
    SystemMessage(content="You are a helpful assistant."),
    HumanMessage(content="What is solar energy?"),
]

response = llm.invoke(messages)  # Returns AIMessage
print(response.content)
```

| Message Type | Purpose | Example |
|-------------|---------|---------|
| `SystemMessage` | Instructions for the LLM's behavior | "You are a lead generation assistant" |
| `HumanMessage` | User input | "I need solar panels" |
| `AIMessage` | LLM response | "What size installation are you looking for?" |
| `ToolMessage` | Result from a tool call | `{next_stage: "discovery"}` |

### Temperature

Temperature controls randomness:

```
temperature=0.0  →  Always the same answer (deterministic)
temperature=0.3  →  Slightly varied (good for business chatbots) ← This project uses this
temperature=0.7  →  Moderately creative (general conversation)
temperature=1.0  →  Very creative (stories, brainstorming)
```

### Practice Task

> **Task**: Create a simple LLM call that asks "What are the benefits of solar energy?" using both OpenAI and Ollama. Compare the responses.
>
> ```python
> from langchain_openai import ChatOpenAI
> from langchain_core.messages import HumanMessage
>
> llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
> response = llm.invoke([HumanMessage(content="What are the benefits of solar energy?")])
> print(response.content)
> ```

---

## Chapter 3 — Prompt Templates

### Why Templates?

Hardcoding prompts is fragile. Templates let you inject dynamic values:

```python
# Bad: Hardcoded
prompt = "You are a greeting assistant. The visitor said: Hi there"

# Good: Template
prompt = "You are a {stage} assistant. The visitor said: {message}"
```

### LangChain Prompt Templates

```python
from langchain_core.prompts import ChatPromptTemplate

template = ChatPromptTemplate.from_messages([
    ("system", "You are a {role} assistant. Be {tone}."),
    ("human", "{user_input}"),
])

messages = template.invoke({
    "role": "lead generation",
    "tone": "professional and friendly",
    "user_input": "I need solar panels",
})

response = llm.invoke(messages)
```

### How This Project Uses Prompts

The project uses a **hybrid approach** — a Python f-string template filled with data from text files:

```python
# Template (in langchain_agent.py)
SYSTEM_PROMPT_TEMPLATE = """You are a professional lead generation assistant.

## Your Conversation Stage: {stage}
{stage_description}

## Stage Advancement Criteria
To advance from "{stage}": {advance_criteria}

## Stage-Specific Prompt
{stage_prompt}

## Tools Available
...
"""

# Filled at runtime
def _build_system_prompt(stage, session_id):
    guide = STAGE_TRANSITION_GUIDE[stage]           # From agent_tools.py
    stage_prompt = _load_stage_prompt(stage)         # From Prompts/Lead/<stage>.txt

    return SYSTEM_PROMPT_TEMPLATE.format(
        stage=stage,
        stage_description=guide["description"],
        advance_criteria=guide["advance_when"],
        stage_prompt=stage_prompt,
        session_id=session_id,
    )
```

### Stage-Specific Prompts

Each stage has its own `.txt` file with focused instructions:

**greeting.txt**:
```
Your goal is ONLY to welcome the visitor and understand why they are here.
Rules:
- Greet politely
- Ask one open-ended question
- Do NOT pitch or sell
- Do NOT ask for contact details yet
```

**contact.txt**:
```
The visitor has shown genuine interest.
Your goal now is to politely collect contact information.
Rules:
- Ask for contact details only AFTER interest is clear
- Explain why the information is needed
- Ask for one detail at a time
```

### Prompt Engineering Tips

```
┌─────────────────────────────────────────────┐
│  Good Prompts Have:                          │
│                                              │
│  1. Clear ROLE     → "You are a ..."        │
│  2. Specific GOAL  → "Your task is to ..."  │
│  3. Explicit RULES → "Do NOT ...", "Always"  │
│  4. Output FORMAT  → "Respond as JSON"       │
│  5. EXAMPLES       → Few-shot examples       │
│  6. CONTEXT        → Stage, history, etc.    │
└─────────────────────────────────────────────┘
```

### Practice Task

> **Task**: Create a LangChain prompt template that takes a `product_name` and `customer_concern` and generates a helpful response.
>
> ```python
> from langchain_core.prompts import ChatPromptTemplate
>
> template = ChatPromptTemplate.from_messages([
>     ("system", "You are a customer support agent for {product_name}. Be helpful and concise."),
>     ("human", "Customer concern: {customer_concern}"),
> ])
>
> messages = template.invoke({
>     "product_name": "SolarMax Panels",
>     "customer_concern": "My panels aren't producing enough energy in winter",
> })
>
> # Then: response = llm.invoke(messages)
> ```

---

## Chapter 4 — Chains

### What is a Chain?

A chain is a sequence of steps where the output of one step feeds into the next. It's like a pipeline:

```
Input → Step 1 → Step 2 → Step 3 → Output
```

### Simple Chain (LCEL — LangChain Expression Language)

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

# Define components
prompt = ChatPromptTemplate.from_messages([
    ("system", "Summarize the following text in one sentence."),
    ("human", "{text}"),
])
llm = ChatOpenAI(model="gpt-4o-mini")
parser = StrOutputParser()

# Chain them with the pipe operator
chain = prompt | llm | parser

# Run the chain
result = chain.invoke({"text": "LangChain is a framework for building AI apps..."})
print(result)  # "LangChain is an AI application development framework."
```

### Chain Diagram

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Prompt   │────>│   LLM    │────>│  Parser  │
│ Template  │     │ (GPT-4)  │     │ (String) │
└──────────┘     └──────────┘     └──────────┘
    Input:           Input:          Input:
    {text}       Messages list    AIMessage
                                     Output:
                                    string
```

### Sequential Chain

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

llm = ChatOpenAI()

# Chain 1: Translate to English
translate = (
    ChatPromptTemplate.from_messages([
        ("system", "Translate the following to English."),
        ("human", "{input}"),
    ])
    | llm
    | StrOutputParser()
)

# Chain 2: Summarize the translation
summarize = (
    ChatPromptTemplate.from_messages([
        ("system", "Summarize this text in 10 words."),
        ("human", "{text}"),
    ])
    | llm
    | StrOutputParser()
)

# Sequential execution
translation = translate.invoke({"input": "Bonjour, comment allez-vous?"})
summary = summarize.invoke({"text": translation})
```

### Structured Output Chain

```python
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

class LeadInfo(BaseModel):
    name: str = Field(description="Customer name")
    email: str = Field(description="Customer email")
    intent: str = Field(description="low, medium, or high")

llm = ChatOpenAI(model="gpt-4o")
structured_llm = llm.with_structured_output(LeadInfo)

result = structured_llm.invoke("My name is John, email is john@example.com, and I'm very interested")
print(result.name)    # "John"
print(result.email)   # "john@example.com"
print(result.intent)  # "high"
```

### How This Project Uses Chains

This project evolved **beyond simple chains** to use an **agent** (Chapter 5). However, the legacy code in `utils.py` shows a simple chain pattern:

```python
# Legacy chain: prompt + LLM → text response
def generate_llm_response(data, prompt, engine):
    base_prompt = load_prompt(prompt, ...)     # Step 1: Load prompt
    summary, duration = generate_with_ollama(data, base_prompt)  # Step 2: Call LLM
    return {"summary": summary, "duration": duration}            # Step 3: Return result
```

### Practice Task

> **Task**: Build a two-step chain that (1) extracts keywords from text and (2) generates a summary using those keywords.
>
> ```python
> from langchain_core.prompts import ChatPromptTemplate
> from langchain_openai import ChatOpenAI
> from langchain_core.output_parsers import StrOutputParser
>
> llm = ChatOpenAI(model="gpt-4o-mini")
>
> # Step 1: Extract keywords
> extract = (
>     ChatPromptTemplate.from_messages([
>         ("system", "Extract 5 keywords from this text. Return comma-separated."),
>         ("human", "{text}"),
>     ]) | llm | StrOutputParser()
> )
>
> # Step 2: Summarize using keywords
> summarize = (
>     ChatPromptTemplate.from_messages([
>         ("system", "Write a one-paragraph summary incorporating these keywords: {keywords}"),
>         ("human", "Original text: {text}"),
>     ]) | llm | StrOutputParser()
> )
>
> text = "Your long article text here..."
> keywords = extract.invoke({"text": text})
> summary = summarize.invoke({"text": text, "keywords": keywords})
> ```

---

## Chapter 5 — Agents

### What is an Agent?

A chain follows a fixed sequence. An **agent** decides its own sequence at runtime. The LLM acts as a "brain" that:

1. **THINKS** about what to do
2. **ACTS** by calling a tool
3. **OBSERVES** the result
4. **Repeats** or generates a final response

This is called the **ReAct** pattern (Reasoning + Acting).

```
┌─────────────────────────────────────────────┐
│              ReAct Agent Loop                │
│                                              │
│  ┌──────────┐                                │
│  │  THINK   │  "I need to check the stage"   │
│  └────┬─────┘                                │
│       ▼                                      │
│  ┌──────────┐                                │
│  │   ACT    │  Call detect_stage tool         │
│  └────┬─────┘                                │
│       ▼                                      │
│  ┌──────────┐                                │
│  │ OBSERVE  │  Tool returned: next="discovery"│
│  └────┬─────┘                                │
│       ▼                                      │
│  ┌──────────┐                                │
│  │  THINK   │  "Now I should respond"        │
│  └────┬─────┘                                │
│       ▼                                      │
│  ┌──────────┐                                │
│  │ RESPOND  │  "Welcome! How can I help?"    │
│  └──────────┘                                │
└─────────────────────────────────────────────┘
```

### Creating a ReAct Agent with LangGraph

```python
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

# 1. Define a tool
@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    # In real life, call a weather API
    return f"The weather in {city} is 72°F and sunny."

# 2. Create the LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0.3)

# 3. Create the agent
agent = create_react_agent(
    model=llm,
    tools=[get_weather],
    checkpointer=MemorySaver(),  # Remembers state across calls
)

# 4. Invoke the agent
result = agent.invoke(
    {"messages": [("human", "What's the weather in Paris?")]},
    config={"configurable": {"thread_id": "session-1"}},
)

# 5. Get the response
for message in result["messages"]:
    print(f"{message.type}: {message.content}")
```

### How This Project's Agent Works

From `langchain_agent.py`:

```python
def build_agent(engine, checkpointer=None):
    llm = get_llm(engine)                    # OpenAI or Ollama

    tools = [
        detect_stage,                         # Advance conversation stage
        stay_in_stage,                        # Stay in current stage
        extract_lead_info,                    # Extract lead data
        get_conversation_history,             # Load chat history from DB
    ]

    if checkpointer is None:
        checkpointer = MemorySaver()

    agent = create_react_agent(
        model=llm,
        tools=tools,
        checkpointer=checkpointer,
    )
    return agent, checkpointer
```

### Agent Execution in This Project

```
invoke_agent() is called
     │
     ├── Build system prompt with stage context
     ├── Load conversation history from PostgreSQL
     │
     └── agent.invoke(messages, config={thread_id: session_id})
              │
              ├── Agent THINKS: "User said they need solar panels.
              │                  Current stage is greeting.
              │                  They've indicated their purpose."
              │
              ├── Agent ACTS: detect_stage("greeting", "I need solar panels", "...")
              │   → Returns: {next_stage: "discovery"}
              │
              ├── Agent ACTS: extract_lead_info(problem="solar panels", intent="low")
              │   → Returns: {problem: "solar panels", intent_level: "low"}
              │
              └── Agent RESPONDS: "That's great! Tell me more about your solar needs."
```

### Agent vs Chain: When to Use Each

| Feature | Chain | Agent |
|---------|-------|-------|
| Execution path | Fixed, predetermined | Dynamic, LLM decides |
| Tool usage | None or sequential | LLM chooses which tools, when |
| Complexity | Lower | Higher |
| Use case | Simple pipelines | Complex decision-making |
| This project | Legacy code | Current architecture |

### Practice Task

> **Task**: Create a simple ReAct agent with two tools: `add(a, b)` and `multiply(a, b)`. Ask it to compute `(3 + 5) * 2`.
>
> ```python
> from langchain_openai import ChatOpenAI
> from langchain_core.tools import tool
> from langgraph.prebuilt import create_react_agent
>
> @tool
> def add(a: int, b: int) -> int:
>     """Add two numbers together."""
>     return a + b
>
> @tool
> def multiply(a: int, b: int) -> int:
>     """Multiply two numbers together."""
>     return a * b
>
> llm = ChatOpenAI(model="gpt-4o-mini")
> agent = create_react_agent(model=llm, tools=[add, multiply])
> result = agent.invoke({"messages": [("human", "What is (3 + 5) * 2?")]})
> ```

---

## Chapter 6 — Tools

### What Are Tools?

Tools are **functions that an agent can call**. The agent reads the tool's name, description, and parameter types, then decides when and how to call it.

### Creating Tools with the @tool Decorator

```python
from langchain_core.tools import tool

@tool
def search_products(query: str, category: str = "all") -> str:
    """Search for products in the catalog.

    Args:
        query: The search term
        category: Product category to filter by (default: all)
    """
    # Your actual search logic here
    return f"Found 5 products matching '{query}' in {category}"
```

**Key points:**
- The **function name** becomes the tool name
- The **docstring** tells the LLM what the tool does and when to use it
- **Type hints** define the parameter schema
- The **return value** is passed back to the LLM as an observation

### This Project's Tools

#### 1. detect_stage — Stage Advancement

```python
@tool
def detect_stage(current_stage: str, user_message: str, conversation_summary: str) -> dict:
    """Decide whether the conversation should advance to the next stage.

    The sales funnel stages are:
      greeting → discovery → qualification → contact → closing

    Returns a dict with current_stage, next_stage, and reasoning.
    """
    guide = STAGE_TRANSITION_GUIDE[current_stage]
    return {
        "current_stage": current_stage,
        "next_stage": guide["next"],
        "reasoning": f"Advanced from {current_stage} to {guide['next']}",
    }
```

#### 2. stay_in_stage — Stay Put

```python
@tool
def stay_in_stage(current_stage: str, reason: str) -> dict:
    """Keep the conversation in the current stage without advancing."""
    return {
        "current_stage": current_stage,
        "next_stage": current_stage,
        "reasoning": f"Staying in {current_stage}: {reason}",
    }
```

#### 3. extract_lead_info — Data Extraction

```python
@tool
def extract_lead_info(name=None, email=None, phone=None, company=None,
                      problem=None, intent_level="low") -> dict:
    """Extract and record lead information mentioned by the visitor.

    IMPORTANT — intent_level MUST be set based on current stage:
      - "low": greeting or discovery
      - "medium": qualification
      - "high": contact or closing
    """
    return {
        "name": name, "email": email, "phone": phone,
        "company": company, "problem": problem,
        "intent_level": intent_level,
    }
```

#### 4. get_conversation_history — Memory Access

```python
@tool
def get_conversation_history(session_id: str) -> str:
    """Retrieve the full conversation history for this session."""
    conversation = Conversation.objects.get(session_id=session_id)
    messages = Message.objects.filter(conversation=conversation).order_by("created_at")

    history = []
    for msg in messages:
        role = "User" if msg.role == "user" else "Assistant"
        history.append(f"{role}: {msg.content}")

    return "\n".join(history)
```

### Tool Design Best Practices

```
┌─────────────────────────────────────────────────┐
│  Good Tool Design                                │
│                                                  │
│  1. Clear, descriptive docstring                 │
│     → The LLM reads this to decide when to call  │
│                                                  │
│  2. Typed parameters with defaults               │
│     → LLM knows what to pass                     │
│                                                  │
│  3. Structured return values                     │
│     → Dict or string that the LLM can reason on  │
│                                                  │
│  4. Idempotent (safe to call multiple times)      │
│     → Agent might retry on error                 │
│                                                  │
│  5. Include "when to call" in the docstring      │
│     → "Call this EVERY turn to evaluate stage"   │
└─────────────────────────────────────────────────┘
```

### Practice Task

> **Task**: Create a `calculate_roi` tool that takes `installation_cost`, `monthly_savings`, and returns the payback period in months.
>
> ```python
> @tool
> def calculate_roi(installation_cost: float, monthly_savings: float) -> str:
>     """Calculate the ROI payback period for a solar installation.
>
>     Args:
>         installation_cost: Total cost of solar panel installation in dollars
>         monthly_savings: Estimated monthly energy savings in dollars
>     """
>     if monthly_savings <= 0:
>         return "Cannot calculate ROI: monthly savings must be positive"
>     months = installation_cost / monthly_savings
>     years = months / 12
>     return f"Payback period: {months:.0f} months ({years:.1f} years)"
> ```

---

## Chapter 7 — Memory

### The Memory Problem

Without memory, every LLM call is stateless. The LLM doesn't know what was said before:

```
Turn 1: User: "My name is John"    → LLM: "Nice to meet you, John!"
Turn 2: User: "What's my name?"    → LLM: "I don't know your name."  ← No memory!
```

### Types of Memory in LangChain

#### 1. Conversation History (Short-term)

The simplest form — just pass all previous messages:

```python
from langchain_core.messages import HumanMessage, AIMessage

history = [
    HumanMessage(content="My name is John"),
    AIMessage(content="Nice to meet you, John!"),
    HumanMessage(content="What's my name?"),  # Current message
]

response = llm.invoke(history)
# → "Your name is John!"
```

#### 2. LangGraph Checkpointer (State Memory)

LangGraph can persist the agent's internal state (including tool call history) across invocations:

```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()  # In-memory storage

agent = create_react_agent(
    model=llm,
    tools=tools,
    checkpointer=checkpointer,
)

# First call
agent.invoke(
    {"messages": [("human", "I'm looking for solar panels")]},
    config={"configurable": {"thread_id": "session-123"}},
)

# Second call — agent remembers the first call!
agent.invoke(
    {"messages": [("human", "For my 10,000 sqft warehouse")]},
    config={"configurable": {"thread_id": "session-123"}},  # Same thread_id
)
```

#### 3. Database-backed History

For production, store messages in a database:

```python
# This project's approach (from langchain_agent.py)
def _load_chat_history(session_id):
    conversation = Conversation.objects.get(session_id=session_id)
    messages = Message.objects.filter(conversation=conversation).order_by("created_at")

    history = []
    for msg in messages[:-1]:  # Exclude last (passed separately)
        if msg.role == "user":
            history.append(HumanMessage(content=msg.content))
        else:
            history.append(AIMessage(content=msg.content))

    return history
```

### How This Project Handles Memory

The project uses a **dual memory strategy**:

```
┌─────────────────────────────────────────────┐
│  Memory Strategy                             │
│                                              │
│  1. PostgreSQL (Source of Truth)              │
│     └── Message table stores all user/bot    │
│         messages with timestamps             │
│     └── Loaded by _load_chat_history()       │
│     └── Survives server restarts             │
│                                              │
│  2. MemorySaver (Agent State)                │
│     └── Stores agent's internal reasoning    │
│         and tool call history                │
│     └── Keyed by thread_id = session_id      │
│     └── Lost on server restart (in-memory)   │
│                                              │
│  Combined: DB provides message history,      │
│  MemorySaver provides agent continuity       │
└─────────────────────────────────────────────┘
```

### Production Memory Options

| Storage | Persistence | Use Case |
|---------|------------|----------|
| `MemorySaver` | In-memory only | Development, testing |
| `PostgresSaver` | PostgreSQL | Production deployment |
| `RedisSaver` | Redis | High-performance, distributed |
| `SqliteSaver` | SQLite file | Simple single-server production |

### Practice Task

> **Task**: Build a chatbot that remembers the user's name across turns using LangGraph's MemorySaver.
>
> ```python
> from langchain_openai import ChatOpenAI
> from langgraph.prebuilt import create_react_agent
> from langgraph.checkpoint.memory import MemorySaver
>
> llm = ChatOpenAI(model="gpt-4o-mini")
> agent = create_react_agent(model=llm, tools=[], checkpointer=MemorySaver())
>
> # Turn 1
> agent.invoke(
>     {"messages": [("human", "My name is Alice")]},
>     config={"configurable": {"thread_id": "test-session"}},
> )
>
> # Turn 2 — does the agent remember?
> result = agent.invoke(
>     {"messages": [("human", "What's my name?")]},
>     config={"configurable": {"thread_id": "test-session"}},
> )
> print(result["messages"][-1].content)  # Should mention "Alice"
> ```

---

## Chapter 8 — Retrieval Augmented Generation (RAG)

### What is RAG?

RAG lets an LLM answer questions about **your own data** by retrieving relevant documents before generating a response.

```
User Question
     │
     ▼
┌───────────┐     ┌──────────────┐     ┌──────────┐
│  Retriever │────>│  Relevant     │────>│   LLM    │
│            │     │  Documents    │     │          │
│  (Vector   │     │  (top 3-5)   │     │ "Based   │
│   Search)  │     │              │     │  on the   │
└───────────┘     └──────────────┘     │  docs..." │
                                       └──────────┘
```

### Why RAG?

LLMs have a knowledge cutoff and don't know your private data. RAG solves this:
- Company knowledge bases
- Product documentation
- Customer records
- Legal documents
- Internal policies

### Building a RAG Pipeline

```python
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader

# 1. Load documents
loader = TextLoader("company_docs.txt")
docs = loader.load()

# 2. Split into chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_documents(docs)

# 3. Create embeddings and store in vector DB
embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(chunks, embeddings)

# 4. Create retriever
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# 5. Build RAG chain
template = ChatPromptTemplate.from_messages([
    ("system", "Answer based on the following context:\n\n{context}"),
    ("human", "{question}"),
])

def rag_answer(question):
    docs = retriever.invoke(question)
    context = "\n\n".join(doc.page_content for doc in docs)
    messages = template.invoke({"context": context, "question": question})
    return llm.invoke(messages).content
```

### RAG Architecture Diagram

```
                ┌──────────────────┐
                │   Documents      │
                │  (PDFs, TXT,     │
                │   Web pages)     │
                └────────┬─────────┘
                         │ Load & Split
                         ▼
                ┌──────────────────┐
                │  Text Chunks     │
                │  (500-1000 chars)│
                └────────┬─────────┘
                         │ Embed
                         ▼
                ┌──────────────────┐
                │  Vector Database │
                │  (Chroma, FAISS, │
                │   Pinecone)      │
                └────────┬─────────┘
                         │
    User Question ───────┤ Similarity Search
                         │
                         ▼
                ┌──────────────────┐
                │  Top K Documents │
                │  (most relevant) │
                └────────┬─────────┘
                         │ Inject into prompt
                         ▼
                ┌──────────────────┐
                │      LLM         │
                │  "Based on the   │
                │   documents..."  │
                └──────────────────┘
```

### This Project's Relationship to RAG

This chatbot project does **not currently use RAG**. It uses stage-specific prompt templates instead of document retrieval. However, RAG could be added to:
- Answer questions about the company's solar products
- Reference pricing documentation
- Access installation guides

### Practice Task

> **Task**: Create a simple RAG system that loads a text file and answers questions about it.
>
> ```python
> from langchain_openai import ChatOpenAI, OpenAIEmbeddings
> from langchain_community.vectorstores import FAISS
> from langchain.text_splitter import CharacterTextSplitter
>
> # Create sample documents
> texts = [
>     "Our solar panels have a 25-year warranty.",
>     "Installation typically takes 2-3 days.",
>     "Average savings are $150/month on electricity.",
>     "We offer financing options with 0% APR for 12 months.",
> ]
>
> # Create vector store
> embeddings = OpenAIEmbeddings()
> vectorstore = FAISS.from_texts(texts, embeddings)
> retriever = vectorstore.as_retriever()
>
> # Ask a question
> docs = retriever.invoke("How long does installation take?")
> print(docs[0].page_content)  # "Installation typically takes 2-3 days."
> ```

---

## Chapter 9 — Production AI Systems

### Moving from Development to Production

```
Development                          Production
┌──────────────────┐                ┌──────────────────┐
│  MemorySaver     │       →        │  PostgresSaver    │
│  (in-memory)     │                │  (persistent)     │
├──────────────────┤                ├──────────────────┤
│  Single process  │       →        │  Multi-worker     │
│                  │                │  (Gunicorn/uWSGI) │
├──────────────────┤                ├──────────────────┤
│  DEBUG=True      │       →        │  DEBUG=False      │
│                  │                │  + proper secrets  │
├──────────────────┤                ├──────────────────┤
│  No monitoring   │       →        │  LangSmith tracing│
│                  │                │  + error tracking  │
├──────────────────┤                ├──────────────────┤
│  print() debug   │       →        │  Structured       │
│                  │                │  logging (JSON)    │
└──────────────────┘                └──────────────────┘
```

### 1. Error Handling

```python
import logging

logger = logging.getLogger(__name__)

def invoke_agent(session_id, user_message, current_stage, engine):
    try:
        agent, checkpointer = get_or_build_agent(engine)
        result = agent.invoke({"messages": messages}, config=config)
        return _parse_agent_result(result, current_stage)

    except Exception as e:
        logger.exception(f"Agent failed for session {session_id}")
        # Return a safe fallback response
        return AgentResponse(
            stage=current_stage,
            response="I'm sorry, I couldn't process that. Please try again.",
            lead=LeadInfo(),
        )
```

### 2. Caching

```python
from django.core.cache import cache

# Cache LLM responses for identical inputs
cache_key = f"llm:{hashlib.sha256(prompt.encode()).hexdigest()}"
cached = cache.get(cache_key)
if cached:
    return cached

result = llm.invoke(prompt)
cache.set(cache_key, result, timeout=3600)  # 1 hour
```

### 3. Rate Limiting and Retries

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4o",
    max_retries=3,              # Retry on transient failures
    request_timeout=30,          # 30 second timeout
    temperature=0.3,
)
```

### 4. Observability with LangSmith

```python
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "ls_..."
os.environ["LANGCHAIN_PROJECT"] = "chatbot-production"

# All LangChain calls are now traced automatically
```

### 5. Security Considerations

```
┌─────────────────────────────────────────────┐
│  Security Checklist                          │
│                                              │
│  □ API keys in environment variables only    │
│  □ Input validation on all user messages     │
│  □ Output sanitization (prevent injection)    │
│  □ Rate limiting per session/IP              │
│  □ CORS properly configured                  │
│  □ CSRF protection (or exemption justified)  │
│  □ Database queries use ORM (no raw SQL)     │
│  □ Prompt injection detection                │
│  □ PII handling compliance                   │
│  □ Logging doesn't include sensitive data    │
└─────────────────────────────────────────────┘
```

### 6. Scaling Architecture

```
                    ┌─────────────┐
                    │   Nginx     │
                    │  (reverse   │
                    │   proxy)    │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ Django   │ │ Django   │ │ Django   │
        │ Worker 1 │ │ Worker 2 │ │ Worker 3 │
        └────┬─────┘ └────┬─────┘ └────┬─────┘
             │             │             │
             └─────────────┼─────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │PostgreSQL│ │  Redis   │ │ LLM API  │
        │  (data)  │ │ (cache)  │ │(provider)│
        └──────────┘ └──────────┘ └──────────┘
```

### Practice Task

> **Task**: Add structured logging and error handling to a LangChain agent invocation.
>
> ```python
> import logging
> import time
>
> logger = logging.getLogger(__name__)
>
> def safe_invoke(agent, messages, session_id):
>     start = time.time()
>     try:
>         result = agent.invoke(
>             {"messages": messages},
>             config={"configurable": {"thread_id": session_id}},
>         )
>         duration = round(time.time() - start, 2)
>         logger.info(f"Agent responded in {duration}s for session {session_id}")
>         return result
>     except Exception as e:
>         duration = round(time.time() - start, 2)
>         logger.error(f"Agent failed after {duration}s: {e}", exc_info=True)
>         raise
> ```

---

## Chapter 10 — Building a Full AI Chatbot

### Putting It All Together

This chapter shows how all the concepts combine in this project to create a production-ready AI chatbot.

### Architecture Summary

```
┌─────────────────────────────────────────────────────────┐
│                  Full Stack AI Chatbot                    │
│                                                          │
│  ┌──────────────────┐    ┌────────────────────────────┐ │
│  │ React Frontend    │    │ Django Backend              │ │
│  │                   │    │                            │ │
│  │ User types        │───>│ views.py: parse request    │ │
│  │ message           │    │                            │ │
│  │                   │    │ langchain_agent.py:        │ │
│  │                   │    │ ├─ Build system prompt     │ │
│  │                   │    │ ├─ Load chat history       │ │
│  │                   │    │ ├─ Invoke ReAct agent      │ │
│  │                   │    │ │  ├─ detect_stage tool    │ │
│  │                   │    │ │  ├─ extract_lead tool    │ │
│  │                   │    │ │  └─ generate response    │ │
│  │                   │    │ └─ Parse agent result      │ │
│  │                   │    │                            │ │
│  │ Display bot       │<───│ views.py: save to DB       │ │
│  │ response          │    │ + return JSON              │ │
│  └──────────────────┘    └────────────────────────────┘ │
│                                                          │
│  ┌──────────────────┐    ┌────────────────────────────┐ │
│  │ PostgreSQL        │    │ LLM Provider               │ │
│  │ Lead, Conv, Msg   │    │ OpenAI / Ollama / LMStudio │ │
│  └──────────────────┘    └────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Step-by-Step: Building Your Own Chatbot

#### Step 1: Define Your Use Case

Before writing code, decide:
- What is the chatbot's purpose? (Lead generation, support, FAQ, etc.)
- What stages/states does the conversation have?
- What data needs to be extracted?
- Which LLM provider will you use?

#### Step 2: Design the Database Schema

```python
# models.py
class Lead(models.Model):
    name = models.CharField(max_length=255, null=True)
    email = models.EmailField(null=True)
    phone = models.CharField(max_length=50, null=True)
    qualified = models.BooleanField(default=False)

class Conversation(models.Model):
    session_id = models.CharField(max_length=255, unique=True)
    stage = models.CharField(max_length=20, default="greeting")
    lead = models.ForeignKey(Lead, null=True, on_delete=models.CASCADE)

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    role = models.CharField(max_length=10)  # "user" or "bot"
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
```

#### Step 3: Create Your Tools

```python
from langchain_core.tools import tool

@tool
def detect_stage(current_stage: str, user_message: str, summary: str) -> dict:
    """Decide whether to advance the conversation stage."""
    # ... stage transition logic
    pass

@tool
def extract_lead_info(name=None, email=None, phone=None) -> dict:
    """Extract lead information from the conversation."""
    return {"name": name, "email": email, "phone": phone}
```

#### Step 4: Write Your Prompts

Create text files for each stage:

```
# prompts/greeting.txt
You are a friendly assistant. Welcome the visitor and ask how you can help.
Do NOT pitch products. Ask ONE open-ended question.
```

#### Step 5: Build the Agent

```python
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

def build_agent(engine):
    llm = get_llm(engine)
    tools = [detect_stage, extract_lead_info, get_history]
    agent = create_react_agent(model=llm, tools=tools, checkpointer=MemorySaver())
    return agent
```

#### Step 6: Create the API Endpoint

```python
@csrf_exempt
@require_http_methods(["POST"])
def chat_api(request):
    body = json.loads(request.body)
    session_id = body["session_id"]
    user_message = body["data"]

    conversation, _ = Conversation.objects.get_or_create(session_id=session_id)
    Message.objects.create(conversation=conversation, role="user", content=user_message)

    result = invoke_agent(session_id, user_message, conversation.stage, "openai")

    Message.objects.create(conversation=conversation, role="bot", content=result.response)
    conversation.stage = result.stage
    conversation.save()

    return JsonResponse({"isSuccess": True, "data": {"response": result.response}})
```

#### Step 7: Build the Frontend

```typescript
// useChat.ts
const sendMessage = async (content: string) => {
    setMessages(prev => [...prev, {role: "user", content}]);
    setLoading(true);

    const reply = await sendChatMessage(sessionId, content);

    setMessages(prev => [...prev, {role: "assistant", content: reply}]);
    setLoading(false);
};
```

### Key Lessons from This Project

1. **Agent > Chain for complex conversations**: The old keyword-based logic got stuck. The LLM agent reasons about context.

2. **Save messages to DB before agent call**: The agent's tools need to read history from the database.

3. **Stage-specific prompts**: Different conversation stages need different LLM behavior.

4. **Intent level maps to stage**: Don't let the LLM guess intent — tie it to the conversation stage.

5. **Singleton agent with MemorySaver**: Reuse the agent across requests to maintain checkpointer state.

6. **Parse tool results from message list**: LangGraph returns all messages including tool calls. Extract what you need.

### Practice Task

> **Task**: Build a minimal chatbot with 3 stages (greeting, question, farewell) and 2 tools (detect_stage, get_user_name). Use Django or Flask for the API and a simple HTML/JS frontend.
>
> Start with:
> 1. Define the 3 stages and their transition criteria
> 2. Create the `detect_stage` and `get_user_name` tools
> 3. Build the ReAct agent with LangGraph
> 4. Create a POST endpoint that accepts `{session_id, message}`
> 5. Return `{stage, response}` as JSON
> 6. Build a simple HTML page with a text input and message list

---

## Appendix: Quick Reference

### Installation

```bash
pip install langchain langchain-core langchain-openai langchain-ollama langgraph
```

### Common Imports

```python
# LLMs
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama

# Messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

# Prompts
from langchain_core.prompts import ChatPromptTemplate

# Tools
from langchain_core.tools import tool

# Agents
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

# Output parsing
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser

# Pydantic for structured output
from pydantic import BaseModel, Field
```

### LangChain Ecosystem Map

```
langchain-core          Base abstractions (messages, prompts, tools)
langchain               High-level chains and utilities
langchain-openai        OpenAI integration (ChatOpenAI, embeddings)
langchain-ollama        Ollama integration (ChatOllama)
langchain-community     Third-party integrations (vector stores, etc.)
langgraph              Agent orchestration (ReAct, state machines)
langsmith              Tracing and observability (optional)
```
