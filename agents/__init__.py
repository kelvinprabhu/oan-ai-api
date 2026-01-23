import logfire

from dotenv import load_dotenv

load_dotenv()
# Configure logfire only if token is present
import os
logfire_token = os.getenv('LOGFIRE_TOKEN')
if logfire_token:
    logfire.configure(token=logfire_token)
else:
    # If no token, logfire will still work locally/silently if configured
    # logfire.configure(send_to_logfire='never')
    pass
logfire.instrument_pydantic_ai()
# logfire.instrument_httpx()