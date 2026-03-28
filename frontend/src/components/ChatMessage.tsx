import Markdown from "react-markdown";

interface Props {
  role: "user" | "assistant";
  content: string;
}

export default function ChatMessage({ role, content }: Props) {
  return (
    <div className={`message ${role}`}>
      <span className="role-label">{role === "user" ? "You" : "Assistant"}</span>
      <div className="msg-content">
        <Markdown>{content}</Markdown>
      </div>
    </div>
  );
}
