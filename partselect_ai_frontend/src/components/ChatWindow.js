import React, { useState, useEffect, useRef, useCallback } from "react";
import "./ChatWindow.css";
import { getAIMessageStream } from "../api/api";
import { marked } from "marked";
import DOMPurify from 'dompurify';
import { format } from "date-fns";

marked.setOptions({
  breaks: true, 
  gfm: true, 
});

function ChatWindow() {
  const defaultMessage = [{
    role: "assistant",
    content: "Hi, how can I help you find refrigerator or dishwasher parts today?",
    timestamp: new Date(),
    id: 'initial-message' 
  }];

  const [messages, setMessages] = useState(defaultMessage);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false); 
  const [isChipVisible, setIsChipVisible] = useState(true);
  const [errorMsg, setErrorMsg] = useState(null); 
  const messagesEndRef = useRef(null);
  const streamCleanerRef = useRef(null); 

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  useEffect(() => {
    return () => {
      if (streamCleanerRef.current) {
        console.log("ChatWindow unmounting, cleaning up active stream.");
        streamCleanerRef.current();
      }
    };
  }, []);

  const handleSend = useCallback(async (messageToSend) => {
    const trimmedInput = typeof messageToSend === 'string' ? messageToSend.trim() : '';
    if (!trimmedInput || isSending) return;

    if (isChipVisible) setIsChipVisible(false);
    setErrorMsg(null); 

    const userMsg = {
      id: `user-${Date.now()}`, 
      role: "user",
      content: trimmedInput,
      timestamp: new Date()
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsSending(true);

    const assistantMsgId = `assistant-${Date.now()}`; 
    const placeholderMsg = {
      id: assistantMsgId,
      role: "assistant",
      content: "", 
      timestamp: null, 
      isLoading: true, 
    };
    setMessages((prev) => [...prev, placeholderMsg]);

    let streamedContent = ""; 

    const onToken = (token) => {
      streamedContent += token;
      console.log(`[ChatWindow] onToken called with: "${token}"`);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMsgId ? { ...msg, content: streamedContent, isLoading: false } : msg // Update content, set loading false on first token
        )
      );
    };

    const onFinish = () => {
      console.log("Stream finished successfully.");
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMsgId
            ? {
                ...msg,
                content: streamedContent.trim(), 
                timestamp: new Date(),
                isLoading: false,
              }
            : msg
        )
      );
      setIsSending(false); 
      streamCleanerRef.current = null; 
    };

    const onError = (error) => {
      console.error("Chat stream error:", error); 
      setErrorMsg('Sorry, I encountered an issue processing your request. Please try again.');
      setMessages((prev) => prev.filter((msg) => msg.id !== assistantMsgId));
      setIsSending(false);
      streamCleanerRef.current = null;
    };

    streamCleanerRef.current = getAIMessageStream(trimmedInput, onToken, onFinish, onError);

  }, [isSending, isChipVisible]);

  const renderSanitizedMarkdown = (content) => {
    const contentString = typeof content === 'string' ? content : '';
    const rawHtml = marked(contentString);
    const sanitizedHtml = DOMPurify.sanitize(rawHtml);
    return { __html: sanitizedHtml };
  };

  return (
    <div className="chat-container"> {/* Use a container class */}
      {/* Optional Header */}
      {/* <header className="chat-header">PartSelect Assistant</header> */}

      <div className="messages-container">
        {messages.map((message) => (
          <div key={message.id} className={`${message.role}-message-container`}>
            <div className={`message ${message.role}-message ${message.isOffTopic ? 'off-topic' : ''}`}>
              <div dangerouslySetInnerHTML={renderSanitizedMarkdown(message.content)}></div>
              {!message.isLoading && message.timestamp && (
                <div className="timestamp">{format(new Date(message.timestamp), 'hh:mm a')}</div>
              )}
              {message.isLoading && <div className="message-loading-indicator">Assistant is thinking...</div>}
            </div>
          </div>
        ))}


        {errorMsg && <div className="error-message">{errorMsg}</div>}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggestion Chips */}
      <div className="suggestion-chips-container">
        { isChipVisible && <button className="suggestion-chip" onClick={() => handleSend("Track my order")}>Track my order</button>}
        { isChipVisible && <button className="suggestion-chip" onClick={() => handleSend("What is the return policy?")}>Return policy</button>}
        { isChipVisible && <button className="suggestion-chip" onClick={() => handleSend("Find a part for model WDT780SAEM1")}>Find part for WDT780SAEM1</button>}
      </div>

      {/* Input Area */}
      <div className="input-area">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about refrigerator or dishwasher parts..."
          onKeyPress={(e) => {
            if (e.key === "Enter" && !e.shiftKey && !isSending) {
              handleSend(input);
              e.preventDefault();
            }
          }}
          disabled={isSending}
        />
        <button
          className="send-button"
          onClick={() => handleSend(input)}
          disabled={isSending || !input.trim()} 
        >
          Send
        </button>
      </div>
    </div>
  );
}

export default ChatWindow;