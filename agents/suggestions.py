from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings
from typing import List
from helpers.utils import get_prompt
from agents.models import LLM_MODEL
from agents.tools.search import search_documents
from pydantic_ai import Tool


from agents.models import LLM_MODEL, LLM_PROVIDER

# Determine prompt file based on provider
prompt_file = 'suggestions_system_groq' if LLM_PROVIDER == 'groq' else 'suggestions_system'

suggestions_agent = Agent(
    name="Suggestions Agent",
    model=LLM_MODEL,
    system_prompt=get_prompt(prompt_file),
    output_type=List[str],
    result_tool_name="suggestions",
    result_tool_description="A list of 3-5 suggested questions for the farmer to ask.",
    retries=1,
    end_strategy='exhaustive',
    tools=[
        Tool(
            search_documents,
            takes_ctx=False,
        )
    ] if LLM_PROVIDER != 'groq' else [],
    model_settings=ModelSettings(
        parallel_tool_calls=False, # Prevent multiple tool calls
    )
)