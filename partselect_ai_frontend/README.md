# PartSelect Chat Agent - Frontend

This repository contains the React-based frontend for the PartSelect Chat Agent, developed as part of the Instalily SWE Case Study. It provides a user interface for interacting with the backend chat agent via a streaming API.

## Features

* **Chat Interface:** Clean and intuitive interface for sending messages and viewing conversation history.
* **Real-time Streaming:** Connects to the backend's Server-Sent Events (SSE) endpoint to display agent responses token-by-token as they are generated.
* **User/Agent Message Display:** Clearly distinguishes between messages sent by the user and responses received from the agent.
* **Session Management:** Handles passing a unique session ID to the backend to maintain conversation context and cart state.
* **Branding:** Basic styling applied to align with PartSelect's visual identity (colors, layout).
* **Suggestion Chips:** Includes suggestion chips for common user actions.

## Tech Stack

* **Framework:** React
* **Language:** JavaScript (or TypeScript, specify if used)
* **Styling:** CSS / Tailwind CSS (specify if used)
* **API Communication:** Browser `fetch` API or Axios
* **Streaming:** Native `EventSource` API for handling Server-Sent Events (SSE)

## Prerequisites

* Node.js (LTS version recommended)
* npm or yarn package manager

## Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd partselect-chat-frontend # Or your frontend directory name
    ```

2.  **Install Dependencies:**
    ```bash
    # Using npm
    npm install

    # Or using yarn
    # yarn install
    ```

3.  **Configure Backend URL (If Necessary):**
    * The application needs to know the URL of the running backend API. By default, it might assume `http://localhost:8000`.
    * Check if there's a `.env` file or configuration setting (e.g., in `src/config.js` or similar) for `REACT_APP_API_URL`.
    * If needed, create a `.env` file in the project root (`partselect-chat-frontend/`) and set the variable:
        ```dotenv
        # .env
        REACT_APP_API_URL=http://localhost:8000
        ```
    * *(Adjust the URL if your backend runs on a different host or port).*

## Running the Application

1.  **Start the development server:**
    ```bash
    # Using npm
    npm start

    # Or using yarn
    # yarn start
    ```

2.  **Access the application:**
    Open your web browser and navigate to `http://localhost:3000` (or the port specified by the start command).

3.  **Interact:** Start typing messages in the chat input to interact with the backend agent. Ensure the backend service is running.

## Key Components (Illustrative)

* `src/App.js`: Main application component, likely manages overall state and layout.
* `src/components/ChatWindow.js`: Component displaying the conversation history.
* `src/components/MessageInput.js`: Component for the user text input and send button.
* `src/services/api.js` (or similar): Module handling communication with the backend API, including the EventSource connection for streaming.

## Limitations & Future Work

* **Frontend Only:** This application relies entirely on the backend service for its logic and responses.
* **Basic UI:** The current UI provides core functionality but could be enhanced.
* **Future Improvements:**
    * More sophisticated loading states and error handling displays.
    * Enhanced UI/UX elements (e.g., clickable links in messages, better product display).
    * Improved accessibility features.
    * End-to-end testing.

