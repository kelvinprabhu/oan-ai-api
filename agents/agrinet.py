from pydantic_ai import Agent, RunContext
from helpers.utils import get_prompt, get_today_date_str
from agents.models import LLM_MODEL
from agents.tools import TOOLS
from pydantic_ai.settings import ModelSettings
from agents.deps import FarmerContext


from agents.models import LLM_PROVIDER
from agents.tools.search import search_documents
from agents.tools.terms import search_terms

# Filter tools for Groq to avoid API errors with specific complex tools
if LLM_PROVIDER == 'groq':
    # Remove search_terms and search_documents
    AGENT_TOOLS = [t for t in TOOLS if t.function.__name__ not in ['search_terms', 'search_documents']]
else:
    AGENT_TOOLS = TOOLS


agrinet_agent = Agent(
    model=LLM_MODEL,
    name="Vistaar Agent",
    output_type=str,
    deps=FarmerContext,
    retries=3,
    tools=AGENT_TOOLS,
    end_strategy='exhaustive',
    model_settings=ModelSettings(
        max_tokens=8192,
        parallel_tool_calls=True,
   )
)

@agrinet_agent.system_prompt
def get_system_prompt(ctx: RunContext[FarmerContext]) -> str:
    from agents.models import LLM_PROVIDER
    # Determine prompt file based on provider
    prompt_file = 'agrinet_system_groq' if LLM_PROVIDER == 'groq' else 'agrinet_system'
    return get_prompt(prompt_file, context={'today_date': get_today_date_str()})