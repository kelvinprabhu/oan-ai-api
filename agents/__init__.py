from h11._abnf import token
import logfire

from dotenv import load_dotenv

load_dotenv()
# logfire.configure(scrubbing=False)
logfire.configure()
logfire.instrument_pydantic_ai()
# logfire.instrument_httpx()