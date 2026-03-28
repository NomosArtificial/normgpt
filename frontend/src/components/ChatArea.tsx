import { useRef, useEffect, useCallback } from "react";
import type { Message } from "../types";
import ChatMessage from "./ChatMessage";
import MessageInput from "./MessageInput";
import LoadingSpinner from "./LoadingSpinner";
import { processSSEStream } from "../hooks/useSSE";
import * as api from "../api";

interface Props {
  convId: string | null;
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  isStreaming: boolean;
  setIsStreaming: (v: boolean) => void;
  streamingText: string;
  setStreamingText: React.Dispatch<React.SetStateAction<string>>;
  onConversationCreated: (id: string) => void;
  refreshConversations: () => void;
}

export default function ChatArea({
  convId,
  messages,
  setMessages,
  isStreaming,
  setIsStreaming,
  streamingText,
  setStreamingText,
  onConversationCreated,
  refreshConversations,
}: Props) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "instant" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingText, scrollToBottom]);

  const doStream = useCallback(
    async (response: Response) => {
      setStreamingText("");
      setIsStreaming(true);

      await processSSEStream(
        response,
        (chunk) => {
          setStreamingText((prev) => prev + chunk);
        },
        () => {},
      );

      setStreamingText((prev) => {
        if (prev) {
          setMessages((msgs) => [...msgs, { role: "assistant", content: prev, created_at: "" }]);
        }
        return "";
      });
      setIsStreaming(false);
    },
    [setMessages, setStreamingText, setIsStreaming],
  );

  const handleSend = useCallback(
    async (content: string) => {
      let id = convId;
      if (!id) {
        const conv = await api.createConversation();
        id = conv.id;
        onConversationCreated(id);
      }

      setMessages((prev) => [...prev, { role: "user", content, created_at: "" }]);

      try {
        const response = await api.chat(id, content);
        if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
        await doStream(response);
        refreshConversations();
      } catch (err) {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: `Error: ${(err as Error).message}`, created_at: "" },
        ]);
      }
    },
    [convId, onConversationCreated, doStream, setMessages, refreshConversations],
  );

  const isEmpty = messages.length === 0 && !convId;

  return (
    <div id="main">
      <div id="messages">
        {isEmpty && <div id="empty-state">Start a new conversation</div>}
        {messages.map((m, i) => (
          <ChatMessage
            key={i}
            role={m.role}
            content={m.content}
          />
        ))}
        {streamingText && <ChatMessage role="assistant" content={streamingText} />}
        {isStreaming && !streamingText && <LoadingSpinner />}
        <div ref={messagesEndRef} />
      </div>
      <MessageInput onSend={handleSend} disabled={isStreaming} />
    </div>
  );
}
