from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from dotenv import load_dotenv
import os

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

# Load .env from root directory
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment variables
base_url = os.getenv("BASE_URL_OLLAMA", "http://localhost:11434")
system_prompt = os.getenv("EX_PROMPT", "You are a helpful AI assistant.")

print(f"Base URL: {base_url}")
print(f"System Prompt Loaded: {system_prompt[:60]}...")

# Initialize LLM
llm = ChatOllama(
    model="kimi-k2.5:cloud",
    base_url=base_url
)

# In-memory session store
store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# Proper prompt structure (System + History + Human)
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])

# Chain
chain = prompt | llm

chat = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history"
)

# Request Models
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

class ClearRequest(BaseModel):
    session_id: str = "default"

# Chat Endpoint
@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        response = chat.invoke(
            {"input": req.message},
            config={"configurable": {"session_id": req.session_id}}
        )
        return {"reply": response.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Clear Single Session
@app.post("/clear")
async def clear_context(req: ClearRequest):
    if req.session_id in store:
        store[req.session_id].clear()
        return {"status": "success", "message": f"Session '{req.session_id}' cleared"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")


# Clear All Sessions
@app.post("/clear_all")
async def clear_all_sessions():
    for session in store.values():
        session.clear()
    store.clear()
    return {"status": "success", "message": "All sessions cleared"}
