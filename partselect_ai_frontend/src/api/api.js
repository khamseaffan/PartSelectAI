import { EventSourcePolyfill } from 'event-source-polyfill';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const getSessionId = () => localStorage.getItem('session_id');

const setSessionId = (sessionId) => {
  if (sessionId) {
    localStorage.setItem('session_id', sessionId);
  } else {
    localStorage.removeItem('session_id');
  }
};

export const getAIMessageStream = (userQuery, onToken, onFinish, onError) => {
  const currentSessionId = getSessionId();
  let eventSource = null;

  let url = `${API_BASE_URL}/stream_chat?message=${encodeURIComponent(userQuery)}`;
  if (currentSessionId) {
    url += `&session_id=${currentSessionId}`;
  }

  console.log(`[API] Connecting to SSE: ${url}`);

  try {
    eventSource = new EventSourcePolyfill(url, {
      headers: {
        'Accept': 'text/event-stream'
      },
      heartbeatTimeout: 30000
    });

    eventSource.onopen = () => {
      console.log("[API] SSE Connection established.");
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.session_id) {
            setSessionId(data.session_id);
        }

        switch (data.type) {
          case 'token':
            if (data.content) {
              onToken(data.content);
            }
            break;
          case 'done':
            eventSource.close(); 
            onFinish(); 
            break;
          case 'error':
            console.error("[API] SSE Error Message Received:", data.content);
            eventSource.close(); 
            if (onError) {
              onError(data.content || 'An unknown error occurred from the server.');
            } else {
              onFinish();
            }
            break;
          default:
            console.warn("[API] Unknown SSE message type received:", data.type, data);
        }
      } catch (err) {
        console.error('[API] Error parsing SSE event data:', err, 'Raw data:', event.data);
         if (onError) {
             onError('Received malformed message from the server.');
         }
      }
    };

    eventSource.onerror = (err) => {
      console.error('[API] EventSource network error or connection failed:', err);
      if (eventSource.readyState === EventSource.CLOSED) {
          console.log("[API] SSE Connection was closed.");
      } else {
          console.error("[API] SSE Network Error Details:", err);
      }
      eventSource.close(); 
      if (onError) {
        onError('Connection to the chat service failed or was interrupted.');
      } else {
        onFinish();
      }
    };

  } catch (error) {
    console.error('[API] Failed to create EventSource:', error);
    if (onError) {
      onError('Failed to connect to the chat service.');
    } else {
      onFinish();
    }
  }

  return () => {
    if (eventSource) {
      console.log("[API] Closing SSE connection via cleanup function.");
      eventSource.close();
    }
  };
};

// export const getAIMessage = async (userQuery) => {
//   try {
//     const res = await fetch("http://localhost:8000/chat", {
//       method: "POST",
//       headers: {
//         "Content-Type": "application/json"
//       },
//       body: JSON.stringify({
//         message: userQuery,
//         session_id: currentSessionId
//       })
//     });

//     const data = await res.json();

//     if (!res.ok) {
//       throw new Error(data.detail || `HTTP error! status: ${res.status}`);
//     }

//     currentSessionId = data.session_id;

//     return {
//       role: "assistant",
//       content: data.response,
//       parts: data.parts || [],
//       isOffTopic: data.is_off_topic || false
//     };
//   } catch (err) {
//     console.error("Error fetching assistant message:", err);
//     return {
//       role: "assistant",
//       content: "I'm having trouble connecting to my knowledge base. Please try again later.",
//       isOffTopic: false,
//       error: true
//     };
//   }
// };

