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

* **For Docker Setup (Recommended):**
    * Docker & Docker Compose installed.
* **For Local Setup (Alternative):**
    * Python 3.9+ installed.
    * UV or Poetry installed (`pip install uv` or Poetry install guide).
    * Redis Server installed and running locally (see platform specifics in Alternative Setup section below).
* **Common:**
    * Access to a Redis instance (local or remote - URL needed for `.env`).
    * API Keys:
        * Deepseek API Key
        * Google API Key (for Custom Search API)
        * Google CSE ID (Programmable Search Engine ID configured for `partselect.com`)
    * Reference for Google Search setup: [LangChain Google Search Docs](https://python.langchain.com/docs/integrations/providers/google/#google-search)

## Setup & Installation

1.  **Clone the repository (if not already done):**
    ```bash
    # If you cloned the parent repo, navigate into the backend directory:
    # cd PartSelectAI/partselect_ai_backend # Adjust path as needed
    # Otherwise, clone just this backend if it's separate:
    # git clone <your-backend-repo-url>
    # cd <backend-directory>
    ```

2.  **Create Environment File:**
    Create a `.env` file in this project's root directory (`partselect_ai_backend/`) and add your API keys and Redis URL:
    ```dotenv
    # .env
    DEEPSEEK_API_KEY="your_deepseek_api_key"
    GOOGLE_API_KEY="your_google_api_key"
    GOOGLE_CSE_ID="your_google_cse_id"
    REDIS_URL="redis://localhost:6379/0" # Adjust if your Redis is elsewhere or running manually
    # DEBUG=True # Optional: for more verbose logging
    ```

3.  **Build and Run with Docker Compose (Recommended):**
    * Ensure Docker Desktop (or Docker Engine + Compose) is running.
    * From this directory (`partselect_ai_backend/`):
    ```bash
    # Ensure .env file is configured
    docker-compose build
    docker-compose up -d # Run in detached mode
    ```
    * The backend should now be running, typically accessible via `http://localhost:8000` (or the port mapped in `docker-compose.yml`).

4.  **Alternative: Running Locally (Without Docker):**
    This method requires manual setup of Python, dependencies, and Redis.

    a.  **Platform-Specific Prerequisites & Setup:**

        * **macOS:**
            * Ensure Python 3.9+ is installed.
            * Install UV (`pip install uv`) or Poetry.
            * Install Redis using Homebrew (if not already installed):
                ```bash
                brew install redis
                ```
            * Start the Redis service using Homebrew:
                ```bash
                brew services start redis
                ```
                *(Verify Redis is running, typically on port 6379).*

        * **Windows:**
            * Ensure Python 3.9+ is installed and added to PATH.
            * Install UV (`pip install uv`) or Poetry.
            * **Redis Setup:** Running Redis natively on Windows requires separate steps. Options include:
                * **WSL (Windows Subsystem for Linux):** Install Redis within your WSL distribution (e.g., `sudo apt update && sudo apt install redis-server` on Ubuntu) and run `sudo service redis-server start`. Ensure your `REDIS_URL` in `.env` points to `redis://localhost:6379`.
                * **Download Windows Port:** Download pre-compiled Windows versions (often older or community-maintained, e.g., from [microsoftarchive/redis releases](https://github.com/microsoftarchive/redis/releases)). Extract and run `redis-server.exe` from the command line in the extracted folder.
                * **Docker:** If you have Docker Desktop for Windows, running Redis in a container (`docker run --name my-redis -p 6379:6379 -d redis`) is often the simplest option.
            * Ensure your chosen Redis instance is running before proceeding.

    b.  **Install Dependencies & Run Server:**
        * Ensure the backend `.env` file is configured in this directory (Step 2 above).
        * **Optional but Recommended:** Create and activate a virtual environment from this directory (`partselect_ai_backend`):
            ```bash
            # Using UV
            uv venv
            # Activate (macOS/Linux): source .venv/bin/activate
            # Activate (Windows CMD): .venv\Scripts\activate.bat
            # Activate (Windows PowerShell): .venv\Scripts\Activate.ps1
            ```
        * Install dependencies using UV (reads `pyproject.toml`):
            ```bash
            uv pip sync
            # OR using Poetry: poetry install
            ```
        * Run the FastAPI server using UV:
            ```bash
            # Ensure virtual environment is active and Redis is running
            uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
            ```
            * The backend should now be running on `http://localhost:8000`.

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

