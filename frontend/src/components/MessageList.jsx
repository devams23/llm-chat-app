import React, { useEffect, useRef } from "react";

export default function MessageList({ messages, loading }) {
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  return (
    <div className="message-list">
      {messages.length === 0 ? (
        <div className="message-empty">
          {loading ? "Loading messages..." : "No messages yet."}
        </div>
      ) : (
        messages.map((message, index) => (
          <div
            key={`${message.role}-${index}`}
            className={`message message-${message.role}`}
          >
            <div className="message-content">{message.content}</div>
          </div>
        ))
      )}
      <div ref={endRef} />
    </div>
  );
}