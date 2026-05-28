import React from "react";

export default function SideBar({
  conversations,
  activeId,
  onSelectConversation,
  onNewChat,
}) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2>Conversations</h2>
        <button type="button" onClick={onNewChat}>
          New Chat
        </button>
      </div>
      {conversations.length === 0 ? (
        <p className="sidebar-empty">No conversations yet.</p>
      ) : (
        <ul className="conversation-list">
          {conversations.map((convo) => (
            <li key={convo.id}>
              <button
                type="button"
                className={`conversation-button${
                  convo.id === activeId ? " is-active" : ""
                }`}
                aria-current={convo.id === activeId ? "true" : undefined}
                onClick={() => onSelectConversation(convo.id)}
              >
                {convo.name ?? `Conversation ${convo.id}`}
              </button>
            </li>
          ))}
        </ul>
      )}
    </aside>
  );
}
