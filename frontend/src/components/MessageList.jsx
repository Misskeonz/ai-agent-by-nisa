import React from 'react';
import './MessageList.css';

const MessageList = ({ messages, isLoading, messagesEndRef }) => {
  return (
    <div className="message-list">
      {messages.length === 0 ? (
        <div className="welcome-message">
          <h2>Welcome to AI Agent Chat!</h2>
          <p>Start a conversation by typing a message below.</p>
        </div>
      ) : (
        messages.map((message) => (
          <div
            key={message.id}
            className={`message message-${message.sender}`}
          >
            <div className="message-header">
              <span className="message-sender">
                {message.sender === 'user' ? 'You' : message.sender === 'ai' ? 'AI Agent' : 'System'}
              </span>
              <span className="message-timestamp">{message.timestamp}</span>
            </div>
            <div className="message-content">
              {message.text}
            </div>
          </div>
        ))
      )}

      {isLoading && (
        <div className="message message-ai">
          <div className="message-header">
            <span className="message-sender">AI Agent</span>
          </div>
          <div className="message-content">
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  );
};

export default MessageList;
