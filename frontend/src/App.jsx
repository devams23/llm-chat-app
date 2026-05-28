
import React, { useState, useEffect } from "react";
import { chatAPI } from "./services/api";
import ChatWindow from "./components/ChatWindow";
import SideBar from "./components/SideBar";
import "./App.css";

function App() {
  const [conversations, setConversations] = useState([]);
  const [activeConversation, setActiveConversation] = useState(null);
  
  useEffect(() => {
    loadConversations();
  }, []);
  
  const loadConversations = async () => {
    //const convos = await chatAPI.listConversations();
    const convos = [{ id: 1, name: "Conversation 1" }];
    setConversations(convos);
    if (convos.length > 0) {
      setActiveConversation((prev) => prev ?? convos[0].id);
    }
  };
  
  const handleNewChat = async () => {
    const newConvo = await chatAPI.createConversation();
    setConversations(prev => [newConvo, ...prev]);
    setActiveConversation(newConvo.id);
  };
  
  return (
    <div className="app">
      <SideBar
        conversations={conversations}
        activeId={activeConversation}
        onSelectConversation={setActiveConversation}
        onNewChat={handleNewChat}
      />
      <main className="chat-area">
        {activeConversation ? (
          <ChatWindow conversationId={activeConversation} />
        ) : (
          <div className="empty-state">Select or start a conversation.</div>
        )}
      </main>
    </div>
  );
}

export default App;
