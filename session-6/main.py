from fastapi import FastAPI
from pydantic import BaseModel
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException

import os

load_dotenv()

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

base_url = os.getenv("BASE_URL_OLLAMA")
system_prompt = os.getenv("EX_PROMPT")

llm = ChatOllama(
    model="kimi-k2.5:cloud",
    base_url=base_url
)

# In-memory store
store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

def add_system_message(messages):
    return [SystemMessage(content=system_prompt)] + messages

chain = RunnableLambda(add_system_message) | llm

chat = RunnableWithMessageHistory(
    chain,
    get_session_history
)

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    response = chat.invoke(
        [HumanMessage(content=req.message)],
        config={"configurable": {"session_id": req.session_id}}
    )
    return {"reply": response.content}


@app.post("/clear")
async def clear_context(session_id: str = "default"):
    if session_id in store:
        store[session_id].clear()  # clears ChatMessageHistory
        return {"status": "success", "message": f"Session '{session_id}' cleared"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")
    

@app.post("/clear_all")
async def clear_all_sessions():
    for session in store.values():
        session.clear()
    store.clear()
    return {"status": "success", "message": "All sessions cleared"}
