import React, { useState } from "react";

export default function MessageInput({ onSend, disabled }) {
  const [text, setText] = useState("");

  const sendMessage = async () => {
    const trimmed = text.trim();
    if (!trimmed || disabled) {
      return;
    }
    setText("");
    await onSend(trimmed);
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    sendMessage();
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  return (
    <form className="message-input" onSubmit={handleSubmit}>
      <textarea
        value={text}
        onChange={(event) => setText(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Type a message..."
        rows={2}
        disabled={disabled}
      />
      <button type="submit" disabled={disabled || !text.trim()}>
        Send
      </button>
    </form>
  );
}