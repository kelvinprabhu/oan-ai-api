# Technical Architecture & Operation Guide

This document provides a comprehensive technical overview of the **MahaVistaar AI API**, including architecture, operation, configuration, and developer onboarding.

---

## 1. API Keys & Secrets

The system relies on various external services. Keys are managed via environment variables (`.env`).

| Service | Environment Variable | Purpose | Required? | Where to Obtain |
| :--- | :--- | :--- | :--- | :--- |
| **App Security** | `SECRET_KEY` | Secures sessions & tokens. | **Yes** | Generate a random strong string (e.g., `openssl rand -hex 32`). |
| **Bhashini** | `MEITY_API_KEY_VALUE` | Indian language translation & voice services. | **Yes** | Bhashini Dashboard (MeitY). |
| **Bhashini** | `BHASHINI_API_KEY` | Alternate/Secondary key for Bhashini services. | Optional | Bhashini Dashboard. |
| **LLM (OpenAI)** | `OPENAI_API_KEY` | Access to GPT-4o/GPT-4-turbo models. | If `LLM_PROVIDER=openai` | [OpenAI Platform](https://platform.openai.com/). |
| **LLM (Gemini)** | `GEMINI_API_KEY` | Access to Google Gemini models. | If `LLM_PROVIDER=gemini` | [Google AI Studio](https://aistudio.google.com/). |
| **LLM (vLLM)** | `INFERENCE_API_KEY` | API key for self-hosted vLLM instance. | If `LLM_PROVIDER=vllm` | Your internal vLLM deployment admin. |
| **vLLM Endpoint** | `INFERENCE_ENDPOINT_URL` | URL for the self-hosted LLM inference server. | If `LLM_PROVIDER=vllm` | Your internal vLLM deployment admin. |
| **Vector DB** | `MARQO_ENDPOINT_URL` | URL of the Marqo vector database instance. | **Yes** | Self-hosted or Marqo Cloud. |
| **Vector DB** | `MARQO_INDEX_NAME` | Name of the Marqo index (e.g., `oan-index`). | **Yes** | Created during Marqo setup. |
| **Mapbox** | `MAPBOX_API_TOKEN` | Geocoding (Address <-> Coordinates). | **Yes** | [Mapbox Dashboard](https://account.mapbox.com/). |
| **Beckn Protocol** | `BAP_ID` | Application ID for ONDC/Beckn network. | **Yes** | ONDC/Beckn Registry. |
| **Beckn Protocol** | `BAP_URI` | Callback URI for ONDC/Beckn network. | **Yes** | Your public callback URL. |
| **Beckn Protocol** | `BAP_ENDPOINT` | Gateway endpoint for Agri services (mandi, weather). | **Yes** | ONDC/Beckn Network Provider. |
| **Sarvam AI** | `SARVAM_API_KEY` | Regional language voice/text services. | Optional | Sarvam AI Dashboard. |
| **ElevenLabs** | `ELEVEN_LABS_API_KEY` | High-quality Text-to-Speech (TTS). | Optional | ElevenLabs Dashboard. |
| **Observability** | `LOGFIRE_TOKEN` | Logging and tracing via Logfire. | Optional | Pydantic Logfire Dashboard. |

### Key Categories

- **LLM Providers**: OpenAI (`OPENAI_API_KEY`), Google Gemini (`GEMINI_API_KEY`), vLLM (`INFERENCE_API_KEY`).
- **Infrastructure**: Marqo (`MARQO_ENDPOINT_URL`), Mapbox (`MAPBOX_API_TOKEN`).
- **Domain Services**: Beckn/ONDC (`BAP_ID`, `BAP_ENDPOINT` - for Weather, Mandi Prices, etc.).
- **Translation/Voice**: Bhashini (`MEITY_API_KEY_VALUE`), Sarvam, ElevenLabs.

---

## 2. Tools & Technologies Used

### Core Stack
| Tool | Category | Role | Why Chosen |
| :--- | :--- | :--- | :--- |
| **FastAPI** | Backend Framework | High-performance async API server. | Native async support, auto-docs (Swagger), lightweight. |
| **Python 3.10+** | Language | Core runtime. | Dominant in AI/ML ecosystem. |
| **Pydantic-AI** | Agent Framework | Orchestrates AI agents and tools. | Type-safe, built on Pydantic, structured output validation. |
| **Redis** | Caching/Memory | Caches user sessions, suggestions, and tool results. | fast in-memory store, supports TTL. |

### Data & AI Infrastructure
| Tool | Category | Role |
| :--- | :--- | :--- |
| **Marqo** | Vector Database | Stores and retrieves embeddings for documents/videos. Handles multimodal search (text-to-video). |
| **Beckn (ONDC)** | Protocol | Standardized protocol to fetch specialized agricultural data (Weather, Market/Mandi prices, Warehouses). |
| **OpenAI / Gemini** | LLM | Provides reasoning capabilities for the agent. |
| **Bhashini** | Translation | Translates user queries (Regional <-> English) and provides Speech-to-Text. |

### Utilities
| Tool | Role |
| :--- | :--- |
| **Pandas** | Data processing for structured data tools. |
| **Geopy** | Geospatial calculations and location handling. |
| **Logfire** | Observability for debugging agent traces. |

---

## 3. AI Agent Architecture

The system is built around a **multi-agent orchestration** pattern using `pydantic-ai`.

### High-Level Components

1.  **Orchestrator (Main App)**: FastAPI handles the websocket/streaming request.
2.  **Moderation Agent**: A specialized lightweight agent that scans inputs for safety and relevance.
3.  **Vistaar Agent (AgriNet)**: The primary cognitive engine that plans and executes tasks.
4.  **Tools Encapsulation**: External APIs (Weather, Market) are wrapped as Python functions exposed to the LLM.

### Architecture Diagram

```mermaid
graph TD
    User[User Request] --> API[FastAPI Chat Endpoint]
    API --> ChatService[Chat Service]
    
    subgraph "Agent Workflow"
        ChatService --> Auth[Context Building]
        Auth --> Mod[Moderation Agent]
        Mod -- "Unsafe" --> Block[Block Request]
        Mod -- "Safe" --> Vistaar[Vistaar Agent (AgriNet)]
        
        Vistaar --> Plan[Reasoning & Planning]
        Plan --> Tools{Tool Selection}
        
        Tools -- "Semantic Search" --> Marqo[(Marqo DB)]
        Tools -- "Geo/Maps" --> Mapbox[Mapbox API]
        Tools -- "Weather/Mandi" --> Beckn[Beckn Gateway]
        
        Tools --> Vistaar
    end
    
    Vistaar --> Stream[Response Stream]
    Stream --> User
```

### Components Detail

1.  **Moderation Agent (`agents/moderation.py`)**:
    - **Input**: User query.
    - **Task**: Classifies query into categories (e.g., `valid_agricultural`, `political_controversial`, `unsafe`).
    - **Model**: Uses a fast model (e.g., Gemini Flash) for low latency.
    - **Output**: Structured `QueryModerationResult`.

2.  **Vistaar Agent (`agents/agrinet.py`)**:
    - **System Prompt**: Context-aware prompt injected with the current date and farmer context.
    - **Tools**: Access to `Search`, `Weather`, `Mandi`, `Network` tools.
    - **Memory**: Short-term conversation history (passed in `messages` list) managed by Redis/Application state.
    - **RAG (Retrieval Augmented Generation)**: Uses the `search_documents` tool to query Marqo for relevant videos and documents when knowledge is required.

---

## 4. Runtime & Execution Flow

### Step-by-Step Request Lifecycle

1.  **Request Entry**:
    - A `POST /api/chat/` request arrives with `query`, `user_id`, `source_lang`, `target_lang`, and `session_id`.
    - FastAPI accepts the request and initiates a `StreamingResponse`.

2.  **Context Preparation**:
    - `stream_chat_messages` (in `app.services.chat`) retrieves previous chat history from Redis/DB.
    - `create_suggestions` is triggered as a background task to generate UI prompts.

3.  **Moderation Check**:
    - The user query is sent to the **Moderation Agent**.
    - If flagged as unsafe, the system refuses to answer immediately.

4.  **Agent Execution**:
    - The **Vistaar Agent** is initialized with `FarmerContext`.
    - The Agent receives the conversation history + new query.
    - **Reasoning Loop**:
        - The LLM decides if it needs data (e.g., "Get weather for Pune").
        - It emits a **Tool Call**.
        - The system executes the tool (e.g., calls `weather_forecast(lat, len)`).
        - The tool result is fed back to the LLM.
        - The LLM processes the data and generates the final natural language response.

5.  **Response Streaming**:
    - The response is streamed token-by-token back to the client via Server-Sent Events (SSE) logic.
    - Final conversation state is saved to history.

---

## 5. Configuration & Environment Setup

### Environment Structure
Create a `.env` file in the root directory.

```bash
# Core
SECRET_KEY=change_this_to_a_secure_random_string
ENVIRONMENT=development

# LLM Selection
LLM_PROVIDER=gemini       # Options: gemini, openai, vllm
LLM_MODEL_NAME=gemini-2.0-flash

# Bhashini (Required for Translation)
MEITY_API_KEY_VALUE=your_bhashini_key

# Vector DB (Marqo)
MARQO_ENDPOINT_URL=http://localhost:8882
MARQO_INDEX_NAME=oan-index

# Beckn / BAP (Agricultural Data)
BAP_ID=vistaar-app
BAP_URI=https://your-callback-url.com/protocol/v1
BAP_ENDPOINT=https://beckn-gateway-url.com

# Mapbox
MAPBOX_API_TOKEN=pk.your_token...

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Local vs Production
- **Local**:
    - Use `LLM_PROVIDER=gemini` (free tier usually available) or `openai`.
    - `REDIS_HOST=localhost` (run via Docker).
    - `MARQO_ENDPOINT_URL` can point to a local Docker container or cloud dev instance.
- **Production**:
    - Use proper `SECRET_KEY`.
    - Set `ENVIRONMENT=production`.
    - Use managed Redis (AWS ElastiCache, etc.).
    - Ensure `BAP_URI` is publicly accessible for Beckn callbacks.

---

## 6. Security & Best Practices

1.  **Key Management**:
    - **NEVER** commit `.env` files to Git.
    - Use a secrets manager (e.g., AWS Secrets Manager) in production, injecting them as env vars.
2.  **Least Privilege**:
    - The API only requires outgoing access to LLM and Tool providers.
    - Database users (Redis/PG) should have restricted permissions if possible.
3.  **Rotation**:
    - Rotate `SECRET_KEY` and API keys periodically (e.g., every 90 days).
4.  **Input/Output**:
    - All user input is moderated via the `Moderation Agent`.
    - Output is streamed to prevent buffering large attacks, but ensure rate limiting (configured in `config.py`) is active.

---

## 7. Getting Started as a New Developer

Welcome! Follow this guide to get the backend running locally.

### Prerequisites
1.  **Python 3.10+** installed.
2.  **Docker & Docker Compose** (for Redis).
3.  **Git**.

### Setup Order

1.  **Clone the Repository**:
    ```bash
    git clone <repo_url>
    cd oan-ai-api
    ```

2.  **Environment Setup**:
    - Copy the example env file:
      ```bash
      cp .env.example .env
      ```
    - **Action**: Fill in at least `LLM_PROVIDER`, `LLM_MODEL_NAME`, associated API key (e.g., `GEMINI_API_KEY`), and `MARQO_ENDPOINT_URL`.

3.  **Install Dependencies**:
    Recommendation: Use a virtual environment.
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # Mac/Linux
    # source venv/bin/activate
    
    pip install -r requirements.txt
    ```

4.  **Start Infrastructure (Redis)**:
    ```bash
    docker-compose up -d redis
    ```

5.  **Run the Application**:
    ```bash
    python main.py
    ```
    server will start at `http://localhost:8000`.

### Verification
- Visit `http://localhost:8000/docs` to see the Swagger UI.
- Use the `/api/health` endpoint to verify the API is up.
- Send a test message via `/api/chat/` (use the "Try it out" feature in Swagger).

### Common Mistakes
- **"Connection Refused" to Redis**: Ensure Docker is running `docker-compose up redis`.
- **"Marqo index not found"**: Ensure your `MARQO_INDEX_NAME` matches what resides in your Marqo instance.
- **"LLM Provider Error"**: Double-check that `LLM_PROVIDER` matches the key you provided (e.g., if provider is `openai`, you must have `OPENAI_API_KEY`).

### Debugging Tips
- Check **logs**: The app logs detailed info to the console. Look for "ERROR" or "WARNING".
- **LLM Traces**: If `logfire` is enabled, check the Logfire dashboard for agent reasoning traces.
- **Tool Failures**: If weather/maps fail, check valid `BAP_ENDPOINT` and `MAPBOX_API_TOKEN` are set.
