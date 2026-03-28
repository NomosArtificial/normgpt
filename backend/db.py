import os
import uuid

import psycopg2  # type: ignore
from contextlib import contextmanager


class ChatDB:
    def __init__(self, dsn: str | None = None):
        self.dsn = dsn or os.environ.get(
            "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/chat"
        )

    @contextmanager
    def _connect(self):
        conn = psycopg2.connect(self.dsn)
        conn.autocommit = False
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init(self):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id SERIAL PRIMARY KEY,
                        conversation_id TEXT NOT NULL REFERENCES conversations(id),
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                """)

    def _rows(self, cur):
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

    def list_conversations(self) -> list[dict]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT c.id, c.title, c.created_at FROM conversations c "
                    "LEFT JOIN messages m ON m.conversation_id = c.id "
                    "GROUP BY c.id "
                    "ORDER BY COALESCE(MAX(m.created_at), c.created_at) DESC"
                )
                return self._rows(cur)

    def create_conversation(self) -> dict:
        conv_id = str(uuid.uuid4())
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO conversations (id, title) VALUES (%s, %s)",
                    (conv_id, "New conversation"),
                )
        return {"id": conv_id, "title": "New conversation"}

    def conversation_exists(self, conv_id: str) -> bool:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM conversations WHERE id = %s", (conv_id,)
                )
                return cur.fetchone() is not None

    def get_messages(self, conv_id: str) -> list[dict]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT role, content, created_at FROM messages "
                    "WHERE conversation_id = %s ORDER BY id",
                    (conv_id,),
                )
                return self._rows(cur)

    def get_history(self, conv_id: str) -> list[dict]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT role, content FROM messages "
                    "WHERE conversation_id = %s ORDER BY id",
                    (conv_id,),
                )
                return self._rows(cur)

    def add_message(self, conv_id: str, role: str, content: str):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO messages (conversation_id, role, content) "
                    "VALUES (%s, %s, %s)",
                    (conv_id, role, content),
                )

    def set_conversation_title(self, conv_id: str, title: str):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE conversations SET title = %s WHERE id = %s",
                    (title, conv_id),
                )

    def delete_conversation(self, conv_id: str):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM messages WHERE conversation_id = %s", (conv_id,))
                cur.execute("DELETE FROM conversations WHERE id = %s", (conv_id,))

