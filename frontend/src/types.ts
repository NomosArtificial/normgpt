export interface Conversation {
  id: string;
  title: string;
  created_at: string;
}

export interface Message {
  role: "user" | "assistant";
  content: string;
  created_at: string;
}
