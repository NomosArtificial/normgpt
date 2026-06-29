from contextlib import asynccontextmanager

import os

import openai
import uvicorn
from fastapi import APIRouter, BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from db import ChatDB

client = openai.OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)
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


class StreamChunk(BaseModel):
    type: str
    content: str = ""


SYSTEM_PROMPT = "You are a helpful assistant."


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


def _stream_response(conv_id: str, messages: list[dict], background_tasks: BackgroundTasks):
    """Stream an OpenAI chat completion."""
    collected = []

    def generate():
        response = client.chat.completions.create(
            model="openai/gpt-4o",
            messages=messages,
            stream=True,
        )

        for chunk in response:
            delta = chunk.choices[0].delta
            if delta.content:
                collected.append(delta.content)
                yield f"data: {StreamChunk(type='text', content=delta.content).model_dump_json()}\n\n"

        background_tasks.add_task(db.add_message, conv_id, "assistant", "".join(collected))
        yield f"data: {StreamChunk(type='done').model_dump_json()}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


def _generate_title(conv_id: str, first_message: str):
    """Generate a conversation title via the LLM."""
    resp = client.chat.completions.create(
        model="openai/gpt-4o-mini",
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


@router.post("/conversations/{conv_id}/chat")
def chat(conv_id: str, req: ChatRequest, background_tasks: BackgroundTasks):
    if not db.conversation_exists(conv_id):
        raise HTTPException(status_code=404, detail="Conversation not found")

    history = db.get_history(conv_id)

    db.add_message(conv_id, "user", req.content)

    if len(history) == 0:
        background_tasks.add_task(_generate_title, conv_id, req.content)

    history.append({"role": "user", "content": req.content})
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    return _stream_response(conv_id, messages, background_tasks)


@router.delete("/conversations/{conv_id}")
def delete_conversation(conv_id: str):
    if not db.conversation_exists(conv_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete_conversation(conv_id)
    return {"ok": True}


app.include_router(router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
