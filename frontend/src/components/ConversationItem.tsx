import type { Conversation } from "../types";

interface Props {
  conversation: Conversation;
  isActive: boolean;
  onSelect: () => void;
  onDelete: () => void;
}

export default function ConversationItem({ conversation, isActive, onSelect, onDelete }: Props) {
  return (
    <div className={`conv-item${isActive ? " active" : ""}`}>
      <span className="conv-title" onClick={onSelect}>
        {conversation.title}
      </span>
      <button
        className="conv-delete"
        title="Delete"
        onClick={(e) => {
          e.stopPropagation();
          onDelete();
        }}
      >
        &times;
      </button>
    </div>
  );
}
