
import React, { useEffect, useState } from "react";
import { chatAPI } from "../services/api";
import MessageInput from "./MessageInput";
import MessageList from "./MessageList";
import ProviderSelector from "./ProviderSelector";

const generateSessionId = () => {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
};

export default function ChatWindow({ conversationId }) {
  const [messages, setMessages] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [sending, setSending] = useState(false);
  const [sessionId] = useState(() => generateSessionId());
  const [provider, setProvider] = useState("");
  const [model, setModel] = useState("");

  useEffect(() => {
    let active = true;
    const loadMessages = async () => {
      if (!conversationId) {
        return;
      }
      setLoadingHistory(true);
      try {
        const response = await chatAPI.getMessages(conversationId);
        if (!active) {
          return;
        }
        const items = Array.isArray(response)
          ? response
          : Array.isArray(response?.messages)
            ? response.messages
            : [];
        const normalized = items.map((item) => ({
          role: item.role ?? item.sender ?? item.type ?? "assistant",
          content: item.content ?? item.message ?? item.text ?? "",
        }));
        setMessages(normalized);
      } catch (error) {
        console.error("Error:", error);
        if (active) {
          setMessages([
            { role: "system", content: "Unable to load messages." },
          ]);
        }
      } finally {
        if (active) {
          setLoadingHistory(false);
        }
      }
    };

    setMessages([]);
    loadMessages();
    return () => {
      active = false;
    };
  }, [conversationId]);

  const handleSendMessage = async (text) => {
    setSending(true);
    setMessages((prev) => [...prev, { role: "user", content: text }]);

    try {
      const response = await chatAPI.sendMessage(
        conversationId,
        text,
        sessionId,
        provider,
        model
      );
      const assistantMessage =
        response?.assistant_message ??
        response?.message ??
        response?.assistant ??
        "";
      if (assistantMessage) {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: assistantMessage },
        ]);
      }
    } catch (error) {
      console.error("Error:", error);
      setMessages((prev) => [
        ...prev,
        { role: "system", content: "Failed to send the message." },
      ]);
    } finally {
      setSending(false);
    }
  };
  
  const handleCancel = async () => {
    try {
      await chatAPI.cancelConversation(conversationId);
      setMessages([]);
    } catch (error) {
      console.error("Error:", error);
    }
  };
  
  const handleStream = async (text) => {
    setSending(true);
    setMessages((prev) => [
      ...prev,
      { role: "user", content: text },
      { role: "assistant", content: "" },
    ]);
    
    const params = new URLSearchParams({
      conversation_id: conversationId,
      session_id: sessionId,
    });
    if (provider) {
      params.set("provider", provider);
    }
    if (model) {
      params.set("model", model);
    }

    const eventSource = new EventSource(
      `/api/chat/send-message-stream?${params.toString()}`
    );
    
    let fullResponse = "";
    
    eventSource.onmessage = (event) => {
      const { chunk } = JSON.parse(event.data);
      fullResponse += chunk;
      
      setMessages(prev => {
        const newMessages = [...prev];
        const lastMessage = newMessages[newMessages.length - 1];
        if (lastMessage?.role === "assistant") {
          lastMessage.content = fullResponse;
        } else {
          newMessages.push({ role: "assistant", content: fullResponse });
        }
        return newMessages;
      });
    };
    
    eventSource.onerror = () => {
      eventSource.close();
      setSending(false);
    };
  };
  
  return (
    <div className="chat-window">
      <div className="actions">
        <ProviderSelector
          onProviderChange={(nextProvider, nextModel) => {
            setProvider(nextProvider);
            setModel(nextModel);
          }}
        />
        <button onClick={handleCancel}>Cancel Conversation</button>
      </div>
      <MessageList messages={messages} loading={loadingHistory} />
      <MessageInput onSend={handleSendMessage} disabled={sending} />
    </div>
  );
}
