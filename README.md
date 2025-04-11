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

* Docker & Docker Compose
* Node.js (LTS recommended) & npm (or yarn)
* Git
* API Keys:
    * Deepseek API Key
    * Google API Key (for Custom Search API)
    * Google CSE ID (Programmable Search Engine ID configured for `partselect.com`)
* reference: https://python.langchain.com/docs/integrations/providers/google/#google-search

### Configuration

1.  **Backend `.env`:** Create a `.env` file in the `/backend` directory with your API keys and Redis URL. See [`backend/README.md`](./backend/README.md) for details.
    ```dotenv
    # backend/.env example
    DEEPSEEK_API_KEY=your_deepseek_api_key
    GOOGLE_API_KEY=your_google_api_key
    GOOGLE_CSE_ID=your_google_cse_id
    REDIS_URL=redis://localhost:6379/0
    ```

### Running the Application

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/khamseaffan/PartSelectAI.git](https://github.com/khamseaffan/PartSelectAI.git)
    cd PartSelectAI
    ```

2.  **Run the Backend (using Docker Compose):**
    * Ensure Docker Desktop (or Engine + Compose) is running.
    * Navigate to the backend directory. *(Adjust directory name if different)*
    ```bash
    cd partselect_ai_backend
    docker-compose build
    docker-compose up -d # Runs backend & associated Redis (if defined)
    cd .. # Go back to the project root
    ```
    * The backend should now be running (typically `http://localhost:8000`).

3.  **Run the Frontend:**
    * Navigate to the frontend directory. *(Adjust directory name if different)*
    ```bash
    cd frontend
    npm install # or yarn install
    npm start   # or yarn start
    ```

4.  **Access the Application:**
    * Open your web browser and navigate to `http://localhost:3000` (or the port specified by the frontend start command).


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
