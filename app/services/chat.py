
from typing import AsyncGenerator
from agents.agrinet import agrinet_agent
from agents.moderation import moderation_agent
from helpers.utils import get_logger
from app.utils import (
    update_message_history, 
    trim_history, 
    format_message_pairs
)
from dotenv import load_dotenv
from agents.deps import FarmerContext
from helpers.utils import get_logger

load_dotenv()

logger = get_logger(__name__)

async def stream_chat_messages(
    query: str,
    session_id: str,
    source_lang: str,
    target_lang: str,
    user_id: str,
    history: list,
) -> AsyncGenerator[str, None]:
    """Async generator for streaming chat messages."""
    # Generate a unique content ID for this query
    content_id = f"query_{session_id}_{len(history)//2 + 1}"
       
    deps = FarmerContext(
        query=query,
        lang_code=target_lang,
    )

    message_pairs = "\n\n".join(format_message_pairs(history, 3))
    if message_pairs:
        last_response = f"**Conversation**\n\n{message_pairs}\n\n---\n\n"
    else:
        last_response = ""
    
    user_message = f"{last_response}{deps.get_user_message()}"
    moderation_run = await moderation_agent.run(user_message)
    moderation_data = moderation_run.output
    
    deps.update_moderation_str(str(moderation_data))

    # Run the main agent
    try:
        async with agrinet_agent.run_stream(
            user_prompt=deps.get_user_message(),
            message_history=trim_history(
                history,
                max_tokens=60_000,
                include_system_prompts=True,
                include_tool_calls=True
            ),
            deps=deps,
        ) as response_stream:  # response_stream is a StreamedRunResult
            async for chunk in response_stream.stream_text(delta=True, debounce_by=0.1): 
                if chunk:  # Ensure non-empty chunks are yielded
                    yield chunk
            
            # After streaming is complete, get the run result for history
            new_messages = response_stream.new_messages()
            messages = [
                *history,
                *new_messages
            ]
            await update_message_history(session_id, messages)

    except Exception as e:
        logger.error(f"Error during streaming for session {session_id}: {str(e)}")
        # If it's a specific tool call error, we can try to fail gracefully
        if "tool call validation failed" in str(e) or "attempted to call tool" in str(e):
             logger.warning(f"Caught tool validation error, falling back to simple response: {e}")
             fallback_msg = "I encountered a technical issue while searching for precise terms, but I will try to answer based on my general knowledge. "
             yield fallback_msg
             # Append a simple text message to history so conversation can continue
             # Note: We can't easily reconstruction the 'partial' tool call that failed, 
             # so we just add the assistant's fallback response.
             messages = [
                *history,
                {"role": "user", "content": query}, # Ensure user query is recorded if not already
                {"role": "model", "content": fallback_msg}
            ]
             await update_message_history(session_id, messages)
        else:
            raise e