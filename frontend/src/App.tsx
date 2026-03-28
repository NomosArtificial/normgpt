import { useState, useEffect, useCallback } from "react";
import type { Conversation, Message } from "./types";
import * as api from "./api";
import Sidebar from "./components/Sidebar";
import ChatArea from "./components/ChatArea";
import "./App.css";

export default function App() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingText, setStreamingText] = useState("");

  const refreshConversations = useCallback(async () => {
    const convs = await api.listConversations();
    setConversations(convs);
    return convs;
  }, []);

  useEffect(() => {
    refreshConversations().then((convs) => {
      if (convs.length > 0) {
        selectConversation(convs[0].id);
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const selectConversation = useCallback(async (id: string) => {
    setActiveConvId(id);
    const msgs = await api.getMessages(id);
    setMessages(msgs);
  }, []);

  const handleNewChat = useCallback(async () => {
    const conv = await api.createConversation();
    setActiveConvId(conv.id);
    setMessages([]);
    await refreshConversations();
  }, [refreshConversations]);

  const handleDelete = useCallback(
    async (id: string) => {
      await api.deleteConversation(id);
      if (activeConvId === id) {
        setActiveConvId(null);
        setMessages([]);
      }
      const convs = await refreshConversations();
      if (activeConvId === id && convs.length > 0) {
        selectConversation(convs[0].id);
      }
    },
    [activeConvId, refreshConversations, selectConversation],
  );

  const handleConversationCreated = useCallback(
    (id: string) => {
      setActiveConvId(id);
      refreshConversations();
    },
    [refreshConversations],
  );

  return (
    <>
      <Sidebar
        conversations={conversations}
        activeConvId={activeConvId}
        onSelect={selectConversation}
        onNewChat={handleNewChat}
        onDelete={handleDelete}
      />
      <ChatArea
        convId={activeConvId}
        messages={messages}
        setMessages={setMessages}
        isStreaming={isStreaming}
        setIsStreaming={setIsStreaming}
        streamingText={streamingText}
        setStreamingText={setStreamingText}
        onConversationCreated={handleConversationCreated}
        refreshConversations={refreshConversations}
      />
    </>
  );
}
