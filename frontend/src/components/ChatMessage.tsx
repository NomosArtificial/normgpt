import Markdown from "react-markdown";

interface Props {
  role: "user" | "assistant";
  content: string;
  streaming?: boolean;
}

export default function ChatMessage({ role, content, streaming }: Props) {
  return (
    <div className={`message ${role}`}>
      <span className="role-label">{role === "user" ? "You" : "Assistant"}</span>
      <div className="msg-content">
        {streaming ? content : <Markdown>{content}</Markdown>}
      </div>
    </div>
  );
}
