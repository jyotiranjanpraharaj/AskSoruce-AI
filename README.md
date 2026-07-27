An advanced meeting and audio AI assistant built with **LangChain (LCEL)**, **Pinecone**, **Groq Whisper**, and **Mistral AI**. 
It downloads audio from YouTube URLs or processes local audio files, transcribes them using Groq Whisper (supporting English, Hindi, and Hinglish), automatically extracts structured deliverables (summaries, action items, key decisions, follow-up questions), and allows semantic Q&A over the transcript using Pinecone.

---

## 🏗️ System Architecture

* **Audio Ingestion**: YouTube URL / Local Audio ➔ `yt-dlp` / RapidAPI Download ➔ FFmpeg Conversion (16kHz mono MP3) ➔ Chunking.
* **Transcription & Extraction**: Audio Chunks ➔ Groq Whisper Cloud API (Transcriptions) ➔ Mistral AI (Summary, Action Items, Key Decisions, and Questions Extraction).
* **RAG Pipeline**: Text Chunks ➔ HuggingFace Embeddings (`all-MiniLM-L6-v2`) ➔ Pinecone Vector Store ➔ Mistral AI Context-Aware QA.

---

## 🛠️ Tech Stack
* **LLM Engine**: Mistral AI API (`mistral-small-latest`, `mistral-small-2506`)
* **Orchestration**: LangChain (Expression Language - LCEL)
* **Speech-to-Text**: Groq Cloud API (Whisper-large-v3)
* **Vector Store**: Pinecone
* **Text Embeddings**: HuggingFace Sentence Transformers (`all-MiniLM-L6-v2`)
* **Audio Engineering**: `yt-dlp` & FFmpeg
* **Backend Framework**: FastAPI & Uvicorn

---

## 📁 Repository Structure
```text
📂 AskSource-AI/
├── 📁 core/                 # Core AI modules (rag_engine, extractor, summarizer, transcriber, vector_store)
├── 📁 utils/                # Audio conversion and download helpers
├── 📁 frontend/             # Static web UI (HTML, CSS, JS)
├── server.py               # FastAPI backend server
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

### 1. Run the Web Server
Start the FastAPI server which also serves the frontend UI:
```bash
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```
* Then open your browser and navigate to `http://localhost:8000` to use the web application.
* Interactive API docs are available at `http://localhost:8000/docs`.
