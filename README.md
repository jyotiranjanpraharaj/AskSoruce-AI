# 🧠 AskSource-AI

An advanced document and meeting AI assistant built with **LangChain (LCEL)**, **FastAPI**, **Chroma DB**, **Groq Whisper**, and **Mistral AI**. It implements two pipelines:
1. **Document RAG Pipeline (FastAPI Backend)**: Ingests documents (PDF, DOCX, TXT, code files, etc.) and performs semantic Q&A with source citations.
2. **Audio/YouTube Pipeline (CLI/Engine)**: Downloads audio from YouTube URLs or local audio files, transcribes them using Groq Whisper (supporting English/Hindi/Hinglish), extracts summaries/action items, and provides semantic Q&A over the transcript.

---

## 🏗️ System Architecture

* **Audio Ingestion**: YouTube URL / Local Audio ➔ `pytubefix` Download ➔ `pydub` (converted to 16kHz mono WAV) ➔ Chunking.
* **Transcription & Extraction**: Audio Chunks ➔ Groq Whisper Cloud API (Transcriptions) ➔ Mistral AI (Summary, Action Items, Key Decisions, and Questions Extraction).
* **RAG Pipeline**: Text Chunks ➔ HuggingFace Embeddings (`all-MiniLM-L6-v2`) ➔ Chroma Vector Store ➔ Mistral AI Context-Aware QA.

---

## 🛠️ Tech Stack
* **LLM Engine**: Mistral AI API (`mistral-small-latest`, `mistral-small-2506`)
* **Orchestration**: LangChain (Expression Language - LCEL)
* **Speech-to-Text**: Groq Cloud API (Whisper-large-v3)
* **Vector Store**: Chroma DB
* **Text Embeddings**: HuggingFace Sentence Transformers (`all-MiniLM-L6-v2`)
* **Audio Engineering**: `pytubefix` & `pydub` (FFmpeg)
* **Backend Framework**: FastAPI & Uvicorn

---

## 📁 Repository Structure
```text
📂 AskSource-AI/
├── 📁 core/                 # Core AI modules (rag_engine, extractor, summarizer, transcriber, vector_store)
├── 📁 utils/                # Audio conversion and download helpers
├── main.py                 # FastAPI server (Document RAG API)
├── run_pipeline.py         # End-to-end CLI runner for YouTube/Audio pipeline
├── test.py                 # Unit tests (Mocked transcriber check)
├── requirements.txt        # Project dependencies
└── .env                    # Environment variables (API keys)
```

---

## 🚀 Installation & Setup

### Prerequisites
* **Python 3.10+**
* **FFmpeg** (Required for audio processing)
  * *Windows* (cmd as Admin): `winget install Gyan.FFmpeg`
  * *macOS*: `brew install ffmpeg`
  * *Ubuntu*: `sudo apt update && sudo apt install ffmpeg`

### Setup Instructions
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/jyotiranjanpraharaj/AskSoruce-AI.git
   cd AskSoruce-AI
   ```

2. **Create and Activate Virtual Environment**:
   ```bash
   python -m venv .venv
   # On Windows (PowerShell):
   .venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**:
   Create a `.env` file in the root folder:
   ```env
   MISTRAL_API_KEY=your_mistral_api_key
   GROQ_API_KEY=your_groq_api_key
   ```

---

## 🖥️ Usage

### 1. Run Audio / YouTube Pipeline
Download a YouTube video/Short, transcribe it, extract deliverables, index it, and run test queries:
```bash
python run_pipeline.py "<YOUTUBE_URL>"
```
*Note: Temporary audio files and chunks are automatically cleaned up after the pipeline runs.*

### 2. Run FastAPI Document Q&A Server
Start the backend for uploading and querying files (PDF, DOCX, TXT):
```bash
python main.py
```
* Interactive docs will be available at `http://127.0.0.1:8000/docs`.

### 3. Run Tests
Verify the transcriber logic using mocked tests:
```bash
python -m unittest test.py
```