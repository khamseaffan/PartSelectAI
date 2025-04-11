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
* **Language:** JavaScript 
* **Styling:** CSS 
* **Streaming:** Native `EventSource` API for handling Server-Sent Events (SSE)

## Prerequisites

* Node.js (LTS version recommended)
* npm package manager

## Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone PartSelectAI
    cd partselect-chat-frontend # Or your frontend directory name
    ```

2.  **Install Dependencies:**
    ```bash
    # Using npm
    npm install

    ```

3.  **Configure Backend URL (Necessary):**
    * The application needs to know the URL of the running backend API. By default, it might assume `http://localhost:8000`.


## Running the Application

1.  **Start the development server:**
    ```bash
    # Using npm
    npm start
    ```

2.  **Access the application:**
    Open your web browser and navigate to `http://localhost:3000` (or the port specified by the start command).

3.  **Interact:** Start typing messages in the chat input to interact with the backend agent. Ensure the backend service is running.

## Key Components (Illustrative)

* `src/App.js`: Main application component, likely manages overall state and layout.
* `src/components/ChatWindow.js`: Component displaying the conversation history.
* `src/components/MessageInput.js`: Component for the user text input and send button.
* `src/services/api.js` : Module handling communication with the backend API, including the EventSource connection for streaming.

## Limitations & Future Work

* **Frontend Only:** This application relies entirely on the backend service for its logic and responses.
* **Basic UI:** The current UI provides core functionality but could be enhanced.

