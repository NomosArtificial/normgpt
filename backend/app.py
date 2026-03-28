from contextlib import asynccontextmanager

import openai
import uvicorn
from fastapi import APIRouter, BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from db import ChatDB

client = openai.OpenAI()
db = ChatDB()


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    content: str


SYSTEM_PROMPT = "You are a helpful assistant."


def _stream_response(conv_id: str, messages: list[dict]):
    """Stream an OpenAI chat completion."""
    collected = []

    def generate():
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            stream=True,
        )

        for chunk in response:
            delta = chunk.choices[0].delta
            if delta.content:
                collected.append(delta.content)
                yield f"data: {delta.content}\n\n"

        yield "data: [DONE]\n\n"

    def save_message():
        full_text = "".join(collected)
        if full_text:
            db.add_message(conv_id, "assistant", full_text)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        background=BackgroundTask(save_message),
    )


def _generate_title(conv_id: str, first_message: str):
    """Generate a conversation title via the LLM."""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Generate a short conversation title (max 6 words) for the following user message. Reply with only the title, no quotes or punctuation at the end.",
            },
            {"role": "user", "content": first_message},
        ],
    )
    title = resp.choices[0].message.content.strip()
    db.set_conversation_title(conv_id, title)


router = APIRouter(prefix="/api")


@router.get("/conversations")
def list_conversations():
    return db.list_conversations()


@router.post("/conversations")
def create_conversation():
    return db.create_conversation()


@router.get("/conversations/{conv_id}/messages")
def get_messages(conv_id: str):
    if not db.conversation_exists(conv_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return db.get_messages(conv_id)


@router.post("/conversations/{conv_id}/chat")
def chat(conv_id: str, req: ChatRequest, background_tasks: BackgroundTasks):
    if not db.conversation_exists(conv_id):
        raise HTTPException(status_code=404, detail="Conversation not found")

    history = db.get_history(conv_id)

    db.add_message(conv_id, "user", req.content)

    # Auto-title on first message using LLM summarization
    if len(history) == 0:
        background_tasks.add_task(_generate_title, conv_id, req.content)

    # Call OpenAI with streaming
    history.append({"role": "user", "content": req.content})
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    return _stream_response(conv_id, messages)


@router.delete("/conversations/{conv_id}")
def delete_conversation(conv_id: str):
    if not db.conversation_exists(conv_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete_conversation(conv_id)
    return {"ok": True}


app.include_router(router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
