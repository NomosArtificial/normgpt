import type { Conversation, Message } from "./types";

const BASE = "/api";

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const opts: RequestInit = {
    method,
    headers: { "Content-Type": "application/json" },
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(`${BASE}${path}`, opts);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export const listConversations = () => request<Conversation[]>("GET", "/conversations");

export const createConversation = () => request<Conversation>("POST", "/conversations");

export const deleteConversation = (id: string) => request<{ ok: boolean }>("DELETE", `/conversations/${id}`);

export const getMessages = (id: string) => request<Message[]>("GET", `/conversations/${id}/messages`);

export const chat = (id: string, content: string) =>
  fetch(`${BASE}/conversations/${id}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
