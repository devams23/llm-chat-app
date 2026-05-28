const API_BASE = "http://localhost:8000/api";

export const chatAPI = {
  createConversation: async () => {
    const response = await fetch(`${API_BASE}/conversations/create`, {
      method: "POST"
    });
    return response.json();
  },
  
  listConversations: async () => {
    const response = await fetch(`${API_BASE}/conversations/list`);
    return response.json();
  },
  
  getMessages: async (conversationId) => {
    const response = await fetch(
      `${API_BASE}/conversations/${conversationId}/messages`
    );
    return response.json();
  },
  
  sendMessage: async (conversationId, message, sessionId, provider, model) => {
    const payload = {
      conversation_id: conversationId,
      message: message,
      session_id: sessionId
    };
    if (provider) {
      payload.provider = provider;
    }
    if (model) {
      payload.model = model;
    }

    const response = await fetch(`${API_BASE}/chat/send-message`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    return response.json();
  },

  getAvailableProviders: async () => {
    const response = await fetch(`${API_BASE}/available-providers`);
    return response.json();
  },

  cancelConversation: async (conversationId) => {
    const response = await fetch(
      `${API_BASE}/conversations/${conversationId}/cancel`,
      { method: "POST" }
    );
    return response.json();
  }
};