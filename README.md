# PartSelect Chat Agent (Instalily SWE Case Study)

This project implements a conversational chat agent designed to assist users with inquiries about Refrigerator and Dishwasher parts on PartSelect.com. It was developed as part of the Software Engineer case study for Instalily.

The agent provides information found via web search, simulates basic shopping cart interactions (add, view, checkout), and guides users to the official PartSelect website for definitive information and purchases.

## Project Components

This project consists of two main parts located in their respective subdirectories:

1.  **Backend (`/backend`)**
    * A Python service built with **FastAPI** using **LangGraph** to manage a ReAct agent powered by the **Deepseek** LLM.
    * Handles core logic, tool execution (Google Search, simulated Cart via **Redis**), state management, and provides a streaming Server-Sent Events (SSE) API.
    * Includes Docker configuration for containerization.
    * **See Backend README  for detailed setup and API information.**

2.  **Frontend (`/frontend`)**
    * A **React** application providing the user interface for the chat agent.
    * Connects to the backend's streaming API using the native `EventSource` API.
    * Features real-time message display and basic PartSelect branding alignment.
    * **See Frontend README for detailed setup and component information.**

## Technology Highlights

* **Frontend:** React, JavaScript/CSS, EventSource API
* **Backend:** Python, FastAPI, LangGraph, Deepseek, Redis, Google Search API, Docker
* **Communication:** Server-Sent Events (SSE) for real-time streaming

## Getting Started

This guide assumes you want to run both the frontend and backend locally.

### Prerequisites

* Docker & Docker Compose (for recommended setup)
* Node.js (LTS recommended) & npm (or yarn)
* Git
* Python 3.9+ (for non-Docker backend setup)
* UV or Poetry (for non-Docker backend setup)
* Redis Server (required if running backend without Docker - see platform specifics below)
* API Keys:
    * Deepseek API Key
    * Google API Key (for Custom Search API)
    * Google CSE ID (Programmable Search Engine ID configured for `partselect.com`)
* Reference for Google Search setup: [LangChain Google Search Docs](https://python.langchain.com/docs/integrations/providers/google/#google-search)

### Configuration

1.  **Backend `.env`:** Before running the backend, create a `.env` file inside the `/backend` (or `/partselect_ai_backend`) directory with your API keys and Redis URL. See backend README for details.
    ```dotenv
    # backend/.env example
    DEEPSEEK_API_KEY=your_deepseek_api_key
    GOOGLE_API_KEY=your_google_api_key
    GOOGLE_CSE_ID=your_google_cse_id
    REDIS_URL=redis://localhost:6379/0 # Ensure this matches your Redis instance if running manually
    ```
2.  **Frontend `.env` (Optional):** If the frontend needs to connect to a backend URL other than the default (likely `http://localhost:8000`), create a `.env` file in the `/frontend` directory *before* starting the frontend. See frontend README for details.
    ```dotenv
    # frontend/.env example
    REACT_APP_API_URL=http://localhost:8000
    ```

### Running the Application

#### Recommended: Using Docker Compose (Backend + Redis)

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/khamseaffan/PartSelectAI.git](https://github.com/khamseaffan/PartSelectAI.git)
    cd PartSelectAI
    ```

2.  **Run the Backend Service:**
    * Ensure Docker Desktop (or Engine + Compose) is running.
    * Navigate to the backend directory:
    ```bash
    cd partselect_ai_backend # Adjust directory name if different
    # Ensure backend .env file is configured (see Configuration section)
    docker-compose build
    docker-compose up -d    # Runs backend & associated Redis (if defined in compose file)
    cd ..                   # Go back to the project root
    ```
    * The backend should now be running (typically `http://localhost:8000`).

3.  **Run the Frontend Service:**
    * Navigate to the frontend directory:
    ```bash
    cd frontend # Adjust directory name if different
    # Ensure frontend .env file is configured if needed (see Configuration section)
    npm install # or yarn install
    npm start   # or yarn start
    ```

4.  **Access the Application:**
    * Open your web browser and navigate to `http://localhost:3000` (or the port specified by the frontend start command).

#### Alternative: Running Backend Locally (Without Docker)

This method requires manual setup of Python, dependencies, and Redis. The frontend still needs to be run separately as described above.

1.  **Platform-Specific Prerequisites & Setup:**

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
            * **Docker:** If you have Docker Desktop for Windows, running Redis in a container (`docker run --name my-redis -p 6379:6379 -d redis`) is often the simplest option, but if you're avoiding Docker Compose entirely, WSL or the Windows port are alternatives.
        * Ensure your chosen Redis instance is running before proceeding.

2.  **Common Steps (Navigate, Install Dependencies, Run Server):**

    * Ensure the backend `.env` file is configured (see Configuration section).
    * Navigate to the backend directory in your terminal:
        ```bash
        cd partselect_ai_backend # Or your backend directory name
        ```
    * **Optional but Recommended:** Create and activate a virtual environment:
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
        * The backend should now be running on `http://localhost:8000`. Remember to also start the frontend separately (Step 3 in the Docker instructions).



## Key Features Summary

* Real-time, streaming chat interface.
* Conversational agent handling Fridge/Dishwasher part inquiries.
* Web search capability for finding parts and information.
* Simulated cart functionality (Add, View).
* Simulated checkout process guiding users to PartSelect.com.
* Scope control (focuses on relevant topics).

## Limitations & Future Work

* **Information Accuracy:** The agent's knowledge is currently limited by the quality and content of Google Search results. Compatibility and troubleshooting answers require verification.
* **Simulated Transactions:** Cart/checkout are session-based simulations via Redis and do not interact with real e-commerce systems.
* **Future Enhancements:**
    * Integrate a structured product database for reliable compatibility.
    * Implement RAG using a vector database for accurate troubleshooting/installation guides.
    * Connect to real PartSelect APIs for live data and functionality.

## Submission Context

This project was developed for the Instalily Software Engineer case study.
