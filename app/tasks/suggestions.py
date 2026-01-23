from app.core.cache import cache
from helpers.utils import get_logger
from app.utils import _get_message_history, trim_history, format_message_pairs
from agents.suggestions import suggestions_agent
from langcodes import Language

logger = get_logger(__name__)


SUGGESTIONS_CACHE_TTL = 60*30 # 30 minutes

async def create_suggestions(session_id: str, target_lang: str = 'mr'):
    """
    Create and save suggestions for a session
    """
    logger.info(f"Getting suggestions for session {session_id}")

    target_lang_name = Language.get(target_lang).display_name(target_lang)

    history   = trim_history(await _get_message_history(session_id),
                             30_000,
                             include_tool_calls=False,
                             include_system_prompts=False
                             )
    message_pairs = "\n\n".join(format_message_pairs(history, 5))

    message       = f"**Conversation**\n\n{message_pairs}\n\n**Based on the conversation, suggest 3-5 questions the farmer can ask in {target_lang_name}.**"
    agent_run    = await suggestions_agent.run(message)
    suggestions = [x for x in agent_run.output]
    
    # Log Suggestions Agent Usage
    sugg_usage = agent_run.usage()
    
    # Extract tool usage if any
    new_messages = agent_run.new_messages()
    tool_calls = [
        msg for msg in new_messages 
        if hasattr(msg, 'parts') and any(part.part_kind == 'tool-call' for part in msg.parts)
    ]
    tool_usage_details = []
    for tc in tool_calls:
         for part in tc.parts:
             if part.part_kind == 'tool-call':
                 tool_usage_details.append(f"{part.tool_name} (args: {part.args})")

    tool_hits_str = "\n    - ".join(tool_usage_details) if tool_usage_details else "None"
    
    logger.info(
        f"\n[Suggestions Agent Usage] Session: {session_id}\n"
        f"  Input Tokens: {sugg_usage.request_tokens}\n"
        f"  Output Tokens: {sugg_usage.response_tokens}\n"
        f"  Total Tokens: {sugg_usage.total_tokens}\n"
        f"  Tool Hits:\n    - {tool_hits_str}"
    )

    logger.info(f"Suggestions: {suggestions}")
    # Store suggestions in cache
    await cache.set(f"suggestions_{session_id}_{target_lang}", suggestions, ttl=SUGGESTIONS_CACHE_TTL)
    logger.info(f"Suggestions created and saved for session {session_id}")
    
    return {
        "status": "success",
        "message": f"Suggestions created and saved for session {session_id}"
    }