# Infrastructure Components Deep Dive

This document details the specific role and configuration of key infrastructure components used in the **Oan-AI-API (MahaVistaar)** project.

---

## 1. Nominatim (The "Map" Engine)

### **What is it?**
**Nominatim** is the open-source search engine that powers **OpenStreetMap (OSM)**. It performs:
- **Geocoding:** Converting addresses/place names (e.g., "Pune", "Shivajinagar") into GPS coordinates (Latitude/Longitude).
- **Reverse Geocoding:** Converting specific GPS coordinates into a human-readable address.

### **Role in this Project**
The project uses Nominatim in `agents/tools/maps.py` to enable the AI agent to understand locations.

*   **Workflow:**
    1.  **User says:** "How is the weather in **Nagpur**?"
    2.  **AI Agent** detects a location entity ("Nagpur").
    3.  **Tool Call:** Calls the `maps` tool.
    4.  **Nominatim:** Converts "Nagpur" → `21.1458, 79.0882`.
    5.  **Beckn Tool:** Uses these coordinates to query the Weather or Mandi Price network (which requires precise lat/long).

### **Configuration (Self-Hosted)**
Unlike many projects that use Google Maps API or Mapbox API, this project is configured to use a **Self-Hosted** version of Nominatim via Docker.

**Code Reference (`agents/tools/maps.py`):**
```python
geocoder = Nominatim(
    user_agent="bharathvistaar", 
    domain="nominatim:8080",  # Points to local Docker container
    scheme="http",
    timeout=10
)
```

### **Why Self-Hosted?**
1.  **No Rate Limits:** Public APIs (OpenStreetMap.org) strictly limit usage (usually 1 request/second). A local instance allows unlimited, high-speed lookups.
2.  **Privacy:** User location queries never leave the internal infrastructure.
3.  **Cost:** Free to run (consumes only server resources), unlike Google Maps which acts on a pay-per-request model.
4.  **Resilience:** Works offline or within an intranet if the map data is pre-loaded.

---

## 2. Marqo (The "Knowledge" Engine)

### **What is it?**
[Marqo](https://www.marqo.ai/) is a specialized **Vector Database** and AI-powered search engine. Unlike traditional SQL databases that match exact text strings, Marqo uses **Vector Embeddings** to understand the *semantic meaning* of data.

### **Role in this Project**
Marqo powers the **RAG (Retrieval-Augmented Generation)** capabilities found in `agents/tools/search.py`.

*   **Workflow:**
    1.  **User asks:** "What is the remedy for leaf curl in chilli?"
    2.  **Marqo Search:** The system converts this query into a vector and searches the database.
    3.  **Semantic Match:** Marqo identifies documents or video transcripts discussing "chilli diseases," "viral infections," and "pesticides," even if the exact phrase "leaf curl" isn't perfectly matched or is described differently in the source.
    4.  **Result:** The agent reads these retrieved snippets to formulate a correct, scientific answer.

### **Why Marqo?**
1.  **Multimodal Support:** Marqo is built to handle **Text** and **Images/Video**. This is critical for agriculture:
    - Farmers often upload photos of sick crops.
    - Marqo can index images and allow the agent to "search" for similar disease patterns visually (future capability).
2.  **Hybrid Search:** It combines **Tensor Search** (AI understanding) with **Lexical Search** (Keyword matching). This ensures that specific terms (e.g., specific pesticide names like "Imidacloprid") are found while still understanding general concepts (e.g., "sucking pests").
3.  **Integrated Embeddings:** Marqo handles the embedding generation internally (using models like specialized BERT or CLIP), simplifying the architecture. You don't need a separate "Embedding Service."

---

## Summary Comparison

| Component | Function | Input Example | Output Example | Key Benefit |
| :--- | :--- | :--- | :--- | :--- |
| **Nominatim** | **Geocoding** | "Nashik, Maharashtra" | `19.9975, 73.7898` | Converts vague user places into precise coordinates for API calls. |
| **Marqo** | **Semantic Search** | "White spots on leaves" | Document: "Fungal infection treatment..." | Finds relevant expert knowledge to ground the AI's answers. |
