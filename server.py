import os
import json
import shutil
import tempfile
import ssl

# Bypass SSL verification globally for urllib and HuggingFace API calls
ssl._create_default_https_context = ssl._create_unverified_context

# Force IPv4 globally for urllib3 to prevent DNS timeouts on dual-stack environments like Render
import socket
import urllib3
urllib3.util.connection.allowed_gai_family = lambda: socket.AF_INET


from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Import core modules
from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarizer import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question, load_rag_chain
from core.vector_store import get_embeddings, load_vector_store, get_retriever

load_dotenv()

app = FastAPI(title="AskSource-AI Video & Audio Assistant API")

# Robust CORS Configuration for Production
origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True if "*" not in origins else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

SESSION_FILE = "session_state.json"

@app.get("/api/status")
async def get_status():
    exists = os.path.exists(SESSION_FILE)
    if exists:
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
            return {
                "active": True,
                "title": state.get("title", "Untitled Audio"),
                "summary": state.get("summary", ""),
                "transcript": state.get("transcript", ""),
                "action_items": state.get("action_items", ""),
                "key_decisions": state.get("key_decisions", ""),
                "open_questions": state.get("open_questions", ""),
                "source_name": state.get("source_name", "Unknown Source")
            }
        except Exception as e:
            return {"active": False, "error": f"Failed to read state: {str(e)}"}
            
    return {"active": False}

@app.post("/api/clear")
async def clear_database():
    try:
        # Delete session state file
        if os.path.exists(SESSION_FILE):
            try:
                os.remove(SESSION_FILE)
            except Exception:
                pass

        # Clear vector database
        try:
            vectorstore = load_vector_store()
            vectorstore.delete(delete_all=True)
        except Exception as e:
            print(f"Warning: Could not clear Pinecone vectors: {e}")

        # Clean up temporary downloads
        if os.path.exists("downloades"):
            for f in os.listdir("downloades"):
                file_path = os.path.join("downloades", f)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception:
                    pass

        return {"status": "success", "message": "Session reset and database cleared successfully."}
    except Exception as e:
        return {"status": "success", "message": f"Database cleared with warning: {str(e)}"}

class QueryRequest(BaseModel):
    question: str

@app.post("/api/process")
async def process_audio(
    youtube_url: str = Form(None),
    language: str = Form("english"),
    file: UploadFile = File(None)
):
    groq_ok = bool(os.getenv("GROQ_API_KEY"))
    mistral_ok = bool(os.getenv("MISTRAL_API_KEY"))
    if not groq_ok or not mistral_ok:
        raise HTTPException(
            status_code=400,
            detail="Groq or Mistral API Keys are not set in backend environment variables."
        )

    if not youtube_url and not file:
        raise HTTPException(
            status_code=400,
            detail="Either youtube_url or file must be provided."
        )

    source = None
    source_name = None

    try:
        if youtube_url:
            source = youtube_url
            source_name = youtube_url
        else:
            # Create downloades directory if not exists
            os.makedirs("downloades", exist_ok=True)
            temp_path = os.path.join("downloades", file.filename)
            with open(temp_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            source = temp_path
            source_name = file.filename

        # Step 1: Download & convert/chunk
        chunks = process_input(source)

        # Step 2: Transcribe via Whisper
        transcript = transcribe_all(chunks, language)
        if not transcript:
            raise ValueError("Whisper transcription returned empty text.")

        # Step 3: Title & summary
        title = generate_title(transcript)
        summary = summarize(transcript)

        # Step 4: Deliverables extraction
        action_items = extract_action_items(transcript)
        key_decisions = extract_key_decisions(transcript)
        open_questions = extract_questions(transcript)

        # Step 5: Index for RAG
        build_rag_chain(transcript)

        # Save session state
        state = {
            "active": True,
            "title": title,
            "summary": summary,
            "transcript": transcript,
            "action_items": action_items,
            "key_decisions": key_decisions,
            "open_questions": open_questions,
            "source_name": source_name
        }
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

        return {
            "status": "success",
            "title": title,
            "summary": summary,
            "transcript": transcript,
            "action_items": action_items,
            "key_decisions": key_decisions,
            "open_questions": open_questions,
            "source_name": source_name
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline processing failed: {str(e)}")

    finally:
        # Guaranteed cleanup of all files in downloades folder to prevent leaks
        if os.path.exists("downloades"):
            for f in os.listdir("downloades"):
                file_path = os.path.join("downloades", f)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception:
                    pass

@app.post("/api/query")
async def query_rag(request: QueryRequest):
    if not os.path.exists(SESSION_FILE):
        raise HTTPException(
            status_code=400,
            detail="No session is active. Please process a video or audio file first."
        )

    if not os.getenv("MISTRAL_API_KEY"):
        raise HTTPException(
            status_code=400,
            detail="MISTRAL_API_KEY environment variable is not set."
        )
        
    try:
        # Get answer
        rag_chain = load_rag_chain()
        answer = ask_question(rag_chain, request.question)

        # Retrieve sources from vector store
        sources = []
        try:
            vectorstore = load_vector_store()
            retriever = get_retriever(vectorstore, k=4)
            docs = retriever.invoke(request.question)
            for i, doc in enumerate(docs):
                chunk_idx = doc.metadata.get("chunk_index", 0)
                sources.append({
                    "index": i + 1,
                    "content": doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content,
                    "page": f"Chunk {chunk_idx + 1}"
                })
        except Exception as e:
            print(f"Warning: Could not retrieve sources for query: {e}")

        return {
            "answer": answer,
            "sources": sources
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying assistant: {str(e)}")

# Serve frontend static files
os.makedirs("frontend", exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def read_index():
    index_path = os.path.join("frontend", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Frontend folder created, but index.html is missing.</h1>")

app.mount("/", StaticFiles(directory="frontend"), name="frontend")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("ENV", "development").lower() == "development"
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=reload)
