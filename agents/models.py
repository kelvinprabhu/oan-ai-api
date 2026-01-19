import os
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.providers.groq import GroqProvider
from dotenv import load_dotenv
from helpers.utils import get_logger

load_dotenv()
logger = get_logger(__name__)

# Get configurations from environment variables
LLM_PROVIDER = os.getenv('LLM_PROVIDER').lower().strip()
LLM_MODEL_NAME = os.getenv('LLM_MODEL_NAME').strip()

# Debug logging
logger.info(f"Initializing LLM - Provider: '{LLM_PROVIDER}', Model: '{LLM_MODEL_NAME}'")

def get_llm_model():
    """Confingure and return the LLM model based on environment settings."""
    
    if LLM_PROVIDER == 'gemini':
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in environment variables")
            
        return GeminiModel(
            LLM_MODEL_NAME,
            provider=GoogleGLAProvider(api_key=api_key)
        )
        
    elif LLM_PROVIDER in ['groq']:
        # Support both GROQ and GROK spelling in keys
        api_key = os.getenv('GROQ_API_KEY') or os.getenv('GROK_API_KEY')
        if not api_key:
            raise ValueError("GROQ_API_KEY (or GROK_API_KEY) is not set in environment variables")
            
        return GroqModel(
            LLM_MODEL_NAME,
            provider=GroqProvider(api_key=api_key)
        )
        
    elif LLM_PROVIDER == 'vllm':
        base_url = os.getenv('INFERENCE_ENDPOINT_URL')
        api_key = os.getenv('INFERENCE_API_KEY', 'empty')
        
        if not base_url:
            raise ValueError("INFERENCE_ENDPOINT_URL is required for vllm provider")
            
        return OpenAIModel(
            LLM_MODEL_NAME,
            provider=OpenAIProvider(
                base_url=base_url, 
                api_key=api_key
            ),
        )
        
    elif LLM_PROVIDER == 'openai':
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set in environment variables")
            
        return OpenAIModel(
            LLM_MODEL_NAME,
            provider=OpenAIProvider(api_key=api_key),
        )
        
    else:
        supported_providers = ['gemini', 'groq', 'vllm', 'openai']
        raise ValueError(f"Invalid LLM_PROVIDER: {LLM_PROVIDER}. Must be one of: {supported_providers}")

try:
    LLM_MODEL = get_llm_model()
    logger.info(f"LLM Model successfully configured: {LLM_MODEL_NAME} via {LLM_PROVIDER}")
except Exception as e:
    logger.critical(f"Failed to configure LLM Model: {str(e)}")
    raise