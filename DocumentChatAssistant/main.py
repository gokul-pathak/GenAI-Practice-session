# backend/main.py

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Any, Dict, List, cast
import os
import io
import supabase

from langchain_ollama import ChatOllama
from rag.embeddings import embeddings
from rag.splitter import text_splitter

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

llm = ChatOllama(
    model="kimi-k2.5:cloud",
    base_url=base_url
)

# -------------------------
# Request Models
# -------------------------
class ChatRequest(BaseModel):
    document_id: str
    message: str


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
        file_bytes = await file.read()

        # 1️⃣ Extract text
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

        # 2️⃣ Store document metadata
        doc_insert = sb_client.table("documents").insert({
            "filename": file.filename
        }).execute()

        if not doc_insert.data:
            raise HTTPException(status_code=500, detail="Failed to insert document")

        rows = cast(List[Dict[str, Any]], doc_insert.data)

        document_id = rows[0]["id"]

        if not document_id:
            raise HTTPException(status_code=500, detail="Document ID missing")


        # 3️⃣ Chunk text
        chunks = text_splitter.split_text(content)

        # 4️⃣ Generate embeddings
        vectors = embeddings.embed_documents(chunks)

        # 5️⃣ Store chunks + embeddings
        for chunk, vector in zip(chunks, vectors):
            sb_client.table("document_chunks").insert({
                "document_id": document_id,
                "content": chunk,
                "embedding": vector
            }).execute()

        return {
            "status": "success",
            "document_id": document_id,
            "chunks_stored": len(chunks)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------
# Query Document Endpoint (REAL RAG)
# -------------------------
@app.post("/query_document")
async def query_document(req: ChatRequest):
    try:
        # 1️⃣ Embed query
        query_embedding = embeddings.embed_query(req.message)

        # 2️⃣ Retrieve relevant chunks via pgvector RPC
        result = sb_client.rpc(
            "match_chunks",
            {
                "query_embedding": query_embedding,
                "match_count": 5,
                "filter_document": req.document_id
            }
        ).execute()

        # 3️⃣ Build context
        if not result.data:
            raise HTTPException(status_code=404, detail="No relevant content found")

        chunks_data = cast(List[Dict[str, Any]], result.data)


        context_parts = []
        source_ids = []

        for row in chunks_data:
            content = row.get("content")
            chunk_id = row.get("id")

            if content:
                context_parts.append(content)
            if chunk_id:
                source_ids.append(chunk_id)

        context = "\n\n".join(context_parts)


        # 4️⃣ Construct final prompt
        prompt = f"""
You are an expert assistant.
Answer ONLY using the provided context.
If the answer is not in the context, say you don't know.

Context:
{context}

Question:
{req.message}
"""

        # 5️⃣ Generate answer
        response = llm.invoke(prompt)
        source_ids = [row["id"] for row in chunks_data]

        return {
            "answer": response.content,
            "sources": source_ids
        }


    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------
# Delete Document + Related Chunks
# -------------------------
@app.delete("/delete_document/{document_id}")
async def delete_document(document_id: str):
    try:
        # 1️⃣ Delete chunks first
        chunks_response = sb_client.table("document_chunks") \
            .delete() \
            .eq("document_id", document_id) \
            .execute()

        # 2️⃣ Delete document
        doc_response = sb_client.table("documents") \
            .delete() \
            .eq("id", document_id) \
            .execute()

        # Optional: check if document existed
        if not doc_response.data:
            raise HTTPException(status_code=404, detail="Document not found")

        return {
            "status": "deleted",
            "deleted_document_id": document_id,
            "deleted_chunks": len(chunks_response.data or [])
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

