# PydanticAI Implementation Guide

This document details how **PydanticAI** is implemented within the Oan-AI-API (MahaVistaar) project. PydanticAI is the core framework used to orchestrate the AI agents, handle tool calling, and manage context.

---

## 1. Why PydanticAI?

We chose PydanticAI for this project because:
1.  **Type Safety:** It is built on top of Pydantic. If an agent returns structured data (like the Moderation Agent), it is guaranteed to match the schema or raise a validation error.
2.  **Dependency Injection:** It has a robust system for passing runtime context (like User ID, Language preference) to the agent without global variables.
3.  **Tooling:** It simplifies wrapping Python functions as "Tools" that LLMs can call.
4.  **Streaming:** It supports streaming responses natively, which is critical for a chat interface.

---

## 2. Core Components

The implementation is split into four distinct layers:

1.  **Dependencies (Context)**: Data passed *into* the agent.
2.  **Tools**: Functions the agent can *call*.
3.  **Agents**: The definitions of the AI personas.
4.  **Execution**: How the application runs the agents.

### A. Dependencies (`agents/deps.py`)

Dependencies act as the "State" for a single run. In this project, `FarmerContext` holds the user's query, language, and moderation results.

```python
# agents/deps.py
class FarmerContext(BaseModel):
    query: str
    lang_code: str = 'mr'
    moderation_str: Optional[str] = None

    def get_user_message(self):
        # dynamic prompt construction based on state
        return f"**User:** {self.query}\n**Language:** {self.lang_code}"
```

### B. Tools (`agents/tools/`)

Tools are standard Python functions. PydanticAI inspects their type hints to generate the function schemas for the LLM.

**Registration (`agents/tools/__init__.py`):**
We explicitly wrap functions using `Tool`.
```python
from pydantic_ai import Tool
from agents.tools.weather import weather_forecast

TOOLS = [
    Tool(weather_forecast, takes_ctx=False),
    # ... other tools
]
```

**Implementation Example (`agents/tools/weather.py`):**
```python
def weather_forecast(latitude: float, longitude: float) -> str:
    """Get Weather forecast for a specific location.
    
    Args:
        latitude (float): Latitude of the location
        longitude (float): Longitude of the location
    """ 
    # Logic to call external API...
    return "Forecast: Sunny, 32C"
```
*Note: The docstring is critical. PydanticAI reads it to tell the LLM **how** and **when** to use the tool.*

### C. Agent Definitions

We have two distinct agents.

#### 1. The Main Agent (`agents/agrinet.py`)
This is a general-purpose agent (Chatbot) that returns a string stream.

```python
# agents/agrinet.py
agrinet_agent = Agent(
    model=LLM_MODEL,          # Configured in agents/models.py
    name="Vistaar Agent",
    output_type=str,          # Return generic text
    deps=FarmerContext,       # Expects this context object at runtime
    tools=TOOLS,              # Available tools
    system_prompt=get_prompt('agrinet_system'),
    retries=3
)
```

#### 2. The Moderation Agent (`agents/moderation.py`)
This is a structured-output agent. It forces the LLM to return a specific JSON result.

```python
# agents/moderation.py
class QueryModerationResult(BaseModel):
    category: Literal["valid_agricultural", "unsafe", ...]
    action: str

moderation_agent = Agent(
    model=LLM_MODEL,
    output_type=QueryModerationResult, # Enforces strict schema
    system_prompt=get_prompt('moderation_system'),
    # ...
)
```

---

## 3. Runtime Execution Flow

The glue that holds this together is in generic service layer, specifically `app/services/chat.py`.

### Step 1: Context Creation & Moderation
Before running the main agent, we run the lightweight moderation agent.

```python
# app/services/chat.py

# 1. Initialize Context
deps = FarmerContext(query=query, lang_code=target_lang)

# 2. Run Moderation (Synchronous-like wait, though async)
moderation_run = await moderation_agent.run(deps.get_user_message())
moderation_data = moderation_run.output # This is a QueryModerationResult object

# 3. Update Context
deps.update_moderation_str(str(moderation_data))
```

### Step 2: Main Agent Streaming
We use `run_stream` to pipe tokens to the user as they are generated.

```python
# app/services/chat.py

async with agrinet_agent.run_stream(
    user_prompt=deps.get_user_message(),
    message_history=history, # Previous messages
    deps=deps,               # Inject dependency
) as response_stream:
    
    # Iterate over tokens
    async for chunk in response_stream.stream_text(delta=True):
        yield chunk

    # 4. Save History
    new_msgs = response_stream.new_messages()
    # Save 'new_msgs' to database...
```

---

## 4. Model Configuration (`agents/models.py`)

PydanticAI supports multiple providers. We abstracted this into a configuration file.

```python
# agents/models.py
LLM_PROVIDER = os.getenv('LLM_PROVIDER')

if LLM_PROVIDER == 'gemini':
    from pydantic_ai.models.gemini import GeminiModel
    LLM_MODEL = GeminiModel('gemini-2.0-flash', ...)
    
elif LLM_PROVIDER == 'openai':
    from pydantic_ai.models.openai import OpenAIModel
    LLM_MODEL = OpenAIModel('gpt-4o', ...)
```

---

## 5. How to Add a New Tool

1.  **Define Function**: Create a new file (e.g., `agents/tools/calculator.py`).
2.  **Type Hints**: Ensure arguments are typed (`int`, `str`) and add a descriptive docstring.
    ```python
    def add(a: int, b: int) -> int:
        """Adds two numbers."""
        return a + b
    ```
3.  **Register**: Import it in `agents/tools/__init__.py`.
    ```python
    TOOLS = [
        # ... existing
        Tool(add)
    ]
    ```
4.  **Restart**: The agent will automatically see the tool in its next run.

---

## 6. How to Modify Agent Behavior

1.  **System Prompt**: Edit `assets/prompts/agrinet_system.txt` (or wherever `get_prompt` pulls from).
2.  **Dependencies**: If the agent needs new runtime data (e.g., User Location), add a field to `FarmerContext` in `agents/deps.py` and populate it in `app/services/chat.py`.

