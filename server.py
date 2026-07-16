import os
import tempfile
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# LangChain Imports
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

app = FastAPI(title="RAG Book Assistant API")

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
PERSIST_DIR = "chroma_db"

def get_embedding_model():
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

import zipfile
import xml.etree.ElementTree as ET
from langchain_core.documents import Document

def load_docx_text(file_path: str) -> str:
    try:
        with zipfile.ZipFile(file_path) as docx:
            xml_content = docx.read('word/document.xml')
        root = ET.fromstring(xml_content)
        paragraphs = []
        for para in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
            texts = [node.text for node in para.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if node.text]
            paragraphs.append(''.join(texts))
        return '\n'.join(paragraphs)
    except Exception as e:
        raise ValueError(f"Failed to read DOCX file: {e}")

@app.get("/api/status")
async def get_status():
    exists = os.path.exists(PERSIST_DIR)
    filename = None
    if exists:
        try:
            embeddings = get_embedding_model()
            vectorstore = Chroma(
                persist_directory=PERSIST_DIR,
                embedding_function=embeddings
            )
            data = vectorstore.get(limit=1)
            if data and 'metadatas' in data and data['metadatas']:
                filename = data['metadatas'][0].get("source")
        except Exception:
            pass
            
    return {
        "database_exists": exists,
        "filename": filename,
        "message": f"Database is active with '{filename}'." if filename else "Database is active." if exists else "No active database. Please upload a document."
    }

@app.post("/api/clear")
async def clear_database():
    if os.path.exists(PERSIST_DIR):
        try:
            shutil.rmtree(PERSIST_DIR)
            return {"status": "success", "message": "Database cleared successfully."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to clear database: {str(e)}")
    return {"status": "success", "message": "Database was already empty."}

class QueryRequest(BaseModel):
    question: str

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    filename = file.filename
    ext = os.path.splitext(filename.lower())[1]
    
    allowed_extensions = {".pdf", ".docx", ".txt", ".md", ".py", ".js", ".json", ".csv", ".html", ".css"}
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file format. Supported formats: {', '.join(allowed_extensions)}"
        )
    
    try:
        # Save file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            temp_path = tmp_file.name
        
        # Load and process document based on extension
        chunks = []
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        if ext == ".pdf":
            loader = PyPDFLoader(temp_path)
            docs = loader.load()
            chunks = splitter.split_documents(docs)
        elif ext == ".docx":
            text = load_docx_text(temp_path)
            doc = Document(page_content=text, metadata={"source": filename})
            chunks = splitter.split_documents([doc])
        else:
            # Plain text files
            with open(temp_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            doc = Document(page_content=text, metadata={"source": filename})
            chunks = splitter.split_documents([doc])
        
        embeddings = get_embedding_model()
        
        # Recreate Chroma vector db (remove old one if it exists to avoid blending different documents)
        if os.path.exists(PERSIST_DIR):
            try:
                shutil.rmtree(PERSIST_DIR)
            except Exception as e:
                pass
                
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=PERSIST_DIR
        )
        vectorstore.persist()
        
        # Clean up temporary file
        os.unlink(temp_path)
        
        return {"status": "success", "message": f"Processed {len(chunks)} text chunks from '{filename}' successfully!"}
    
    except Exception as e:
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")

@app.post("/api/query")
async def query_rag(request: QueryRequest):
    if not os.path.exists(PERSIST_DIR):
        return {
            "answer": "No document has been uploaded yet. Please upload a PDF book first to build the vector database.",
            "sources": []
        }
    
    if not os.getenv("MISTRAL_API_KEY"):
        raise HTTPException(
            status_code=400, 
            detail="MISTRAL_API_KEY environment variable is not set. Please add it to your .env file."
        )
        
    try:
        embeddings = get_embedding_model()
        vectorstore = Chroma(
            persist_directory=PERSIST_DIR,
            embedding_function=embeddings
        )
        
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 6},
        )
        
        docs = retriever.invoke(request.question)
        if not docs:
            return {
                "answer": "I could not find the answer in the document.",
                "sources": []
            }
        
        context = "\n\n".join([doc.page_content for doc in docs])
        
        llm = ChatMistralAI(model="mistral-small-2506")
        
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are a helpful AI assistant.\n\nUse the provided context as the primary source to answer the question.\n\nIf the context does not contain enough information, say:\n\"I could not find the answer in the document.\"\n"
            ),
            (
                "human",
                "Context:\n{context}\n\nQuestion:\n{question}\n"
            )
        ])
        
        final_prompt = prompt.invoke({
            "context": context,
            "question": request.question
        })
        
        response = llm.invoke(final_prompt)
        
        # Prepare sources metadata to show in UI
        sources = []
        for i, doc in enumerate(docs):
            page = doc.metadata.get("page", 0) + 1  # 0-indexed page to 1-indexed
            sources.append({
                "index": i + 1,
                "content": doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content,
                "page": page
            })
            
        return {
            "answer": response.content,
            "sources": sources
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying assistant: {str(e)}")

# Serve frontend static files
# Make sure frontend directory exists
os.makedirs("frontend", exist_ok=True)

# Mount index.html at root route
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
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
