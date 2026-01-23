# Project Onboarding: OpenAgriNet (MahaVistaar AI API)

Welcome to the **OpenAgriNet (OAN)** project! This is the backend for **MahaVistaar**, an AI-driven agricultural assistant designed to help farmers in Maharashtra.

## 1. High-Level Overview

### **What problem does this solve?**
It democratizes access to expert agricultural knowledge. Instead of navigating complex government websites or physical offices, farmers can ask questions (e.g., "What is the market price of onions in Pune?" or "It's raining, what should I do with my cotton crop?") in their native language (Marathi/English) and get instant, accurate, location-specific advice.

### **Tech Stack**
*   **Language:** Python 3.12+
*   **Web Framework:** FastAPI (Async, High-performance)
*   **Server:** Uvicorn (dev) / Gunicorn (prod)
*   **AI Framework:** **`pydantic-ai`** (A modern, type-safe agentic framework)
*   **LLM Providers:** OpenAI, Sarvam AI, potentially local models (Ollama).
*   **Database/Cache:** Redis (for caching sessions and health checks).
*   **Search Engine:** Marqo (Vector search, likely for RAG - Retrieval Augmented Generation).
*   **Infrastructure:** Docker & Docker Compose.
*   **External Integration:** **Beckn Protocol (ONDC)** for standardized communication with agricultural networks (Weather, Mandis, Storage).

### **Architecture Overview**
The project follows a **Service-Oriented Architecture** with a strong emphasis on **Agentic Patterns**.
1.  **API Layer (`app/`)**: Handles HTTP requests, authentication, and routing.
2.  **Service Layer (`app/services/`)**: Orchestrates the flow between the API and the AI agents.
3.  **Agent Layer (`agents/`)**: The "Brain". Uses LLMs to understand intent and select tools.
4.  **Tool Layer (`agents/tools/`)**: Interfaces with the outside world (Weather APIs, Market databases) using standard protocols.

---

## 2. Folder Structure Analysis

### **Root Directory**
*   **`main.py`**: **Entry Point**. Initializes the FastAPI app, middleware (CORS), and includes all routers.
*   **`.env.example`**: **Critical**. Template for environment variables. You cannot run the app without a properly configured `.env` file.
*   **`docker-compose.yml`**: Defines the services (API, Redis, Marqo, Nominatim) for local development.
*   **`requirements.txt`**: Python dependencies.

### **`app/` (The Application Shell)**
*   **`routers/`**: Contains the API endpoints.
    *   **`chat.py`**: The core endpoint. Handles user queries, manages sessions, and streams responses.
    *   **`transcribe.py` / `tts.py`**: Voice processing endpoints (Speech-to-Text / Text-to-Speech).
*   **`services/`**: Bridges routers and agents.
    *   **`chat.py`**: Contains `stream_chat_messages`. This is where the request is prepared (context creation) and sent to the AI agent.
*   **`config.py`**: **Configuration Central**. Reads `.env` variables using `pydantic-settings`.
*   **`core/cache.py`**: Redis connection and caching logic.

### **`agents/` (The AI Brain)**
This is where the magic happens.
*   **`agrinet.py`**: **The Main Agent**. Defines `agrinet_agent` using `pydantic_ai`. It tells the LLM what `tools` are available and sets the system prompt.
*   **`deps.py`**: **Context**. Defines `FarmerContext`. This acts as the "state" passed to the agent (User query, selected language, moderation results).
*   **`moderation.py`**: A separate agent/logic to check if the user's query is safe/relevant before processing.
*   **`tools/`**: **The Hands**. Actual Python functions the agent can call.
    *   `weather.py`: Fetches weather data.
    *   `mandi.py`: Fetches market prices.
    *   `warehouse.py`: Finds storage.
    *   *Note: These tools appear to format requests in the **Beckn Protocol (ONDC)** standard, suggesting this app is a client (BAP) in a larger ONDC network.*

---

## 3. Key Files Explained

| File | Importance | Description |
| :--- | :--- | :--- |
| **`app/config.py`** | 🚨 Critical | All settings (API keys, URLs, DB configs). **Must read** to understand external dependencies. |
| **`agents/agrinet.py`** | 🧠 Core Logic | Defines the "Persona" of the AI. Modify this to change how the bot behaves or what tools it has access to. |
| **`app/routers/chat.py`** | 🚪 Entry | Understanding `chat(...)` and its `background_tasks` is key to debugging the request flow. |
| **`agents/tools/weather.py`** | 🛠 Example Tool | Shows how the AI fetches external data. It constructs complex JSON payloads for the Beckn network. |
| **`agents/deps.py`** | 📦 State | Defines what data makes it into the prompt context (`FarmerContext`). |

---

## 4. Mental Model: How a Request Flows

1.  **User** sends a POST request to `/api/chat` with: `"What is the weather in Nashik?"`.
2.  **`app/routers/chat.py`**:
    *   Generates a Session ID.
    *   Retrieves message history (for context).
    *   Calls `stream_chat_messages`.
3.  **`app/services/chat.py`**:
    *   Runs a quick **Moderation Check** (`moderation_agent`).
    *   Initializes `FarmerContext` (lang=Marathi/English, query="...").
    *   **Invokes `agrinet_agent.run_stream(...)`**.
4.  **`agents/agrinet.py`** (The Agent):
    *   LLM analyzes the query.
    *   **Decision:** "I need weather data." -> Calls `weather_forecast(lat, long)`.
5.  **`agents/tools/weather.py`**:
    *   Constructs a **Beckn Protocol** JSON request.
    *   Sends HTTP POST to an external `BAP_ENDPOINT` (e.g., government weather node).
    *   Receives JSON response, uses Pydantic to parse it, and converts it to a text summary.
6.  **The Agent**:
    *   Receives the text summary from the tool.
    *   Synthesizes a final natural language answer for the farmer.
7.  **Output**: The answer is **streamed** back to the user token-by-token.

---

## 5. Architectural Patterns

*   **Agentic Workflow:** The app interacts with the world via **Tools**. The logic isn't hardcoded; the LLM decides *which* function to call based on the user's intent.
*   **Streaming Responses:** To keep the UI snappy for long LLM generations, everything is built to stream using `AsyncGenerator` and `StreamingResponse`.
*   **Beckn Protocol (ONDC):** The tools are designed to talk to a decentralized network. This is a complex protocol involving `context`, `message`, `intent` structures seen in `weather.py`.

---

## 6. Onboarding Guide for New Developers

### **Setup**
1.  **Env Vars:** Copy `.env.example` to `.env`. You will need API keys for:
    *   `OPENAI_API_KEY` (or other LLM provider).
    *   `BAP_ENDPOINT` (for the tools to work).
    *   `MAPBOX_API_TOKEN` (for location services).
2.  **Docker:** The easiest way to run is `docker compose up`. This spins up Redis, Marqo, and the API.
3.  **Local Run:**
    ```bash
    pip install -r requirements.txt
    uvicorn main:app --reload
    ```

### **Common Pitfalls**
*   **Tool Errors:** If the external Beckn network (`BAP_ENDPOINT`) is down or misconfigured, the tools (`weather.py`, `mandi.py`) will fail or return generic errors. The agent might hallucinate if tool outputs are confusing.
*   **Context Limit:** Watch out for the message history size in `app/services/chat.py`. It trims history to `60_000` tokens, which is generous but can be expensive.
*   **Async/Await:** Everything is async. If you block the event loop (e.g., using `time.sleep` instead of `asyncio.sleep`), the entire API will freeze.

### **Areas for Improvement (Tech Debt)**
*   **Tool Complexity:** The specialized Beckn JSON construction inside `agents/tools/*.py` is verbose and hard to maintain. It couples the agent logic tightly to specific external API formats.
*   **Hardcoded URLs:** Some URLs in `config.py` or tools might be hardcoded to specific dev environments.
*   **Error Handling:** If a tool fails, the agent's recovery strategy relies on the LLM interpreting the error string.
