# PartSelect Chat Agent - Backend

This repository contains the backend service for the PartSelect Chat Agent, developed as part of the Instalily SWE Case Study. It features a conversational agent powered by Deepseek and LangGraph, designed to assist users with refrigerator and dishwasher parts inquiries on PartSelect.com.

## Features

* **Conversational Agent:** Uses LangGraph and the ReAct pattern with the Deepseek LLM for understanding requests and orchestrating responses.
* **Tool Usage:** Integrates tools for:
    * Searching PartSelect.com via Google Search API (`SearchPartSelectKeywords`).
    * Simulated shopping cart management (`AddToCart`, `ViewCart`).
    * Simulated checkout process (`Checkout`).
    * Providing help links and return policy info (`HelpLinks`, `ReturnPolicy`).
* **Streaming API:** Provides a Server-Sent Events (SSE) endpoint (`/stream_chat`) for real-time responses to the frontend.
* **Session Management:** Utilizes Redis to maintain conversation state and simulated cart contents per user session.
* **Focused Scope:** Designed to handle inquiries related to refrigerator and dishwasher parts only, politely declining off-topic requests (guided by system prompt).
* **Containerized:** Includes Dockerfile and docker-compose for easy setup and deployment.

## Tech Stack

* **Language:** Python 3.9+
* **Framework:** FastAPI
* **Agent Orchestration:** LangGraph
* **LLM:** Deepseek (via `langchain-deepseek`)
* **Tools:** LangChain Core, Google Search API (`langchain-google-community`)
* **State Management:** Redis
* **API Server:** Uvicorn
* **Containerization:** Docker, Docker Compose
* **Dependency Management:** Poetry / UV (as indicated by `pyproject.toml` and `uv.lock`)

## Prerequisites

* Docker & Docker Compose installed.
* Access to a Redis instance (local or remote).
* API Keys:
    * Deepseek API Key
    * Google Search API Key
    * Google Programmable Search Engine ID (CSE ID) configured to search `partselect.com`.

## Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd partselect_ai_backend # Or your backend directory name
    ```

2.  **Create Environment File:**
    Create a `.env` file in the project root directory (`partselect_ai_backend/`) and add your API keys and Redis URL:
    ```dotenv
    # .env
    DEEPSEEK_API_KEY="your_deepseek_api_key"
    GOOGLE_API_KEY="your_google_api_key"
    GOOGLE_CSE_ID="your_google_cse_id"
    REDIS_URL="redis://localhost:6379/0" # Adjust if your Redis is elsewhere
    # DEBUG=True # Optional: for more verbose logging
    ```

3.  **Build and Run with Docker Compose:** (Recommended)
    Ensure Docker Desktop (or Docker Engine + Compose) is running.
    ```bash
    docker-compose build
    docker-compose up -d # Run in detached mode
    ```
    The backend should now be running, typically accessible via `http://localhost:8000` (or the port mapped in `docker-compose.yml`).

4.  **Alternative Setup (Without Docker, using Poetry/UV):**
    * Ensure Python 3.9+ and Poetry are installed.
    * Install dependencies:
        ```bash
        # Using Poetry
        poetry install
        # Or using UV (if installed)
        # uv pip install -r requirements.txt # Assuming an export exists, or:
        # uv venv # Create venv
        # uv pip sync pyproject.toml # Sync based on pyproject
        ```
    * Ensure Redis is running and accessible at the URL specified in `.env`.
    * Run the application using Uvicorn:
        ```bash
        # Activate virtual environment if needed (e.g., poetry shell or source .venv/bin/activate)
        uvicorn main:app --host 0.0.0.0 --port 8000 --reload
        ```

## Configuration

Environment variables are managed via the `.env` file (see Setup). Key variables:

* `DEEPSEEK_API_KEY`: Your API key for the Deepseek service.
* `GOOGLE_API_KEY`: Your Google Cloud API key enabled for the Custom Search API.
* `GOOGLE_CSE_ID`: The ID of your Google Programmable Search Engine configured for PartSelect.
* `REDIS_URL`: Connection string for your Redis instance.

## API Endpoint

* **`GET /stream_chat`**
    * **Description:** Main endpoint for interacting with the chat agent. Uses Server-Sent Events (SSE) for streaming responses.
    * **Query Parameters:**
        * `message` (str, required): The user's message.
        * `session_id` (str, optional): A UUID string representing the user session. If not provided, a new one is generated.
    * **Responses:** Streams JSON objects via SSE with fields like `type` ("token", "done", "error") and `content`.

## Project Structure

partselect_ai_backend/├── agents/             # Agent logic, tools definition, system prompt│   ├── agent.py│   └── tools.py├── routes/             # API route definitions│   └── chat.py├── .env                # Environment variables (API keys, Redis URL) - !! NOT COMMITTED !!├── Dockerfile          # Docker build instructions├── docker-compose.yml  # Docker Compose service definitions├── main.py             # FastAPI application entry point├── pyproject.toml      # Project metadata and dependencies (for Poetry/UV)├── redis_manager.py    # Handles interactions with Redis└── uv.lock             # Lock file for dependencies (UV)
## Limitations & Future Work

* **Accuracy:** Relies on Google Search results for part information, compatibility, and troubleshooting, which may be inaccurate or incomplete.
* **Simulated Transactions:** Cart and checkout functionalities are simulated within the session using Redis and do not interact with real PartSelect systems.
* **Future Improvements:**
    * Integrate a structured product database for reliable compatibility checks.
    * Implement RAG using a vector database and PartSelect manuals/guides for accurate troubleshooting.
    * Connect to real PartSelect APIs (if available) for live data and real transactions.

