import type { Conversation } from "../types";
import ConversationItem from "./ConversationItem";

interface Props {
  conversations: Conversation[];
  activeConvId: string | null;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  onDelete: (id: string) => void;
}

export default function Sidebar({ conversations, activeConvId, onSelect, onNewChat, onDelete }: Props) {
  return (
    <div id="sidebar">
      <button id="new-chat-btn" onClick={onNewChat}>
        + New Chat
      </button>
      <div id="conv-list">
        {conversations.map((c) => (
          <ConversationItem
            key={c.id}
            conversation={c}
            isActive={c.id === activeConvId}
            onSelect={() => onSelect(c.id)}
            onDelete={() => onDelete(c.id)}
          />
        ))}
      </div>
    </div>
  );
}
