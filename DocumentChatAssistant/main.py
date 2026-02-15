# backend/main.py

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import uuid
import io
import supabase

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

# -------------------------
# Load Environment Variables
# -------------------------
load_dotenv()


def get_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"{name} is not set in environment variables.")
    return value


SUPABASE_URL = get_env("SUPABASE_URL")
SUPABASE_KEY = get_env("SUPABASE_KEY")
sb_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------
# FastAPI Setup
# -------------------------
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# LLM Setup
# -------------------------
base_url = os.getenv("BASE_URL_OLLAMA", "http://localhost:11434")
system_prompt = os.getenv(
    "EX_PROMPT",
    "You are a helpful assistant for answering questions based on uploaded documents."
)

llm = ChatOllama(model="kimi-k2.5:cloud", base_url=base_url)

# -------------------------
# In-Memory Stores (Temporary)
# -------------------------
chat_store: dict[str, ChatMessageHistory] = {}
document_store: dict[str, dict] = {}


def get_session_history(session_id: str) -> ChatMessageHistory:
    if session_id not in chat_store:
        chat_store[session_id] = ChatMessageHistory()
    return chat_store[session_id]


prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])

chain = prompt | llm
chat = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history"
)

# -------------------------
# Request Models
# -------------------------
class ChatRequest(BaseModel):
    document_id: str
    message: str
    session_id: str = "default"


class ClearRequest(BaseModel):
    session_id: str = "default"


# -------------------------
# Helper: Extract File Extension
# -------------------------
def get_file_extension(filename: str | None) -> str:
    if not filename or "." not in filename:
        raise HTTPException(status_code=400, detail="File must have a valid filename and extension")
    return filename.rsplit(".", 1)[-1].lower()


# -------------------------
# Upload Document Endpoint
# -------------------------
@app.post("/upload_document")
async def upload_document(file: UploadFile = File(...)):
    try:
        ext = get_file_extension(file.filename)
        doc_id = str(uuid.uuid4())
        storage_filename = f"{doc_id}_{file.filename}"
        file_bytes = await file.read()
        content = ""

        if ext == "txt":
            content = file_bytes.decode("utf-8")
        elif ext == "pdf":
            import pdfplumber
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                content = "\n".join(page.extract_text() or "" for page in pdf.pages)
        elif ext == "docx":
            from docx import Document
            doc = Document(io.BytesIO(file_bytes))
            content = "\n".join(p.text for p in doc.paragraphs)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        sb_client.storage.from_("documents").upload(storage_filename, file_bytes)

        document_store[doc_id] = {
            "filename": file.filename,
            "storage_path": storage_filename,
            "text": content
        }

        return {"status": "success", "document_id": doc_id, "filename": file.filename}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------
# Query Document Endpoint
# -------------------------
@app.post("/query_document")
async def query_document(req: ChatRequest):
    if req.document_id not in document_store:
        raise HTTPException(status_code=404, detail="Document not found")

    doc_text = document_store[req.document_id]["text"]
    query_prompt = f"""
Use the following document to answer the question.

Document:
{doc_text}

Question:
{req.message}
"""

    try:
        response = chat.invoke({"input": query_prompt}, config={"configurable": {"session_id": req.session_id}})
        return {"reply": response.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------
# Clear Chat Session and Delete Document
# -------------------------
@app.post("/clear")
async def clear_context(req: ClearRequest):
    # Clear chat session
    if req.session_id in chat_store:
        chat_store[req.session_id].clear()

    # Delete all documents from memory and Supabase
    removed_docs = []
    for doc_id, doc in list(document_store.items()):
        try:
            # Remove from Supabase storage
            sb_client.storage.from_("documents").remove([doc["storage_path"]])
        except Exception as e:
            # Log but continue
            print(f"Error deleting {doc['storage_path']} from storage: {e}")
        removed_docs.append(doc["filename"])
        # Remove from in-memory store
        del document_store[doc_id]

    return {
        "status": "success",
        "message": f"Session '{req.session_id}' cleared",
        "deleted_documents": removed_docs
    }
