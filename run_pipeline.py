import os
import sys
import shutil
from dotenv import load_dotenv

# Reconfigure stdout to support UTF-8 on Windows command lines
sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarizer import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question

def main():
    # YouTube URL from user
    youtube_url = "https://youtube.com/shorts/LHWxNjD6wdY?si=DKS9TsfL0g7wPuIO"
    if len(sys.argv) > 1:
        youtube_url = sys.argv[1]
        
    print(f"=== Starting Audio RAG Pipeline for URL: {youtube_url} ===")
    
    # Check API keys
    if not os.getenv("GROQ_API_KEY"):
        print("Error: GROQ_API_KEY is not set in environment or .env file.")
        sys.exit(1)
    if not os.getenv("MISTRAL_API_KEY"):
        print("Error: MISTRAL_API_KEY is not set in environment or .env file.")
        sys.exit(1)
        
    # Step 1: Process Audio (Download, Convert, Chunk)
    print("\n--- Step 1: Processing Audio (Downloading & Chunking) ---")
    chunks = []
    try:
        chunks = process_input(youtube_url)
    except Exception as e:
        print(f"Error during audio processing: {e}")
        cleanup_download_dir()
        sys.exit(1)
        
    if not chunks:
        print("Error: No audio chunks were created.")
        cleanup_download_dir()
        sys.exit(1)
        
    # Step 2: Transcribe chunks using Groq Whisper
    print("\n--- Step 2: Transcribing Audio (using Groq Whisper) ---")
    try:
        # We'll use Hinglish as the video is related to Dharma/Sanatan Dharma and may contain Hindi/English mixed terms
        transcript = transcribe_all(chunks, language="hinglish")
        print("\n--- Transcript Generated ---")
        print(transcript)
    except Exception as e:
        print(f"Error during transcription: {e}")
        cleanup_download_dir()
        sys.exit(1)
        
    if not transcript.strip():
        print("Error: Generated transcript is empty.")
        cleanup_download_dir()
        sys.exit(1)

    # Step 3: Summarize and Extract Information using Mistral AI
    print("\n--- Step 3: Generating Title, Summary, and Extracts ---")
    try:
        title = generate_title(transcript)
        print(f"\nTitle: {title}")
        
        summary = summarize(transcript)
        print(f"\nSummary:\n{summary}")
        
        action_items = extract_action_items(transcript)
        print(f"\nAction Items:\n{action_items}")
        
        key_decisions = extract_key_decisions(transcript)
        print(f"\nKey Decisions:\n{key_decisions}")
        
        questions = extract_questions(transcript)
        print(f"\nQuestions/Follow-ups:\n{questions}")
    except Exception as e:
        print(f"Error during extraction/summarization: {e}")
        cleanup_download_dir()
        sys.exit(1)
        
    # Step 4: Build Vector Store and Query RAG Chain
    print("\n--- Step 4: Building Vector Store and Running RAG Query ---")
    try:
        # Build RAG chain (indexes transcript chunks to vector db)
        rag_chain = build_rag_chain(transcript)
        
        # Run a sample query
        sample_query = "What does the video say about dharma?"
        print(f"\nQuerying RAG: '{sample_query}'")
        answer = ask_question(rag_chain, sample_query)
        print(f"\nAnswer:\n{answer}")
        
        # Ask another sample query
        sample_query_2 = "What should parents teach or do?"
        print(f"\nQuerying RAG: '{sample_query_2}'")
        answer_2 = ask_question(rag_chain, sample_query_2)
        print(f"\nAnswer:\n{answer_2}")
        
    except Exception as e:
        print(f"Error in RAG engine: {e}")
    finally:
        # Cleanup audio chunks and downloads
        cleanup_download_dir()
        print("\n=== Pipeline execution complete. Audio files cleaned up. ===")

def cleanup_download_dir():
    print("\nCleaning up download directory...")
    download_dir = 'downloades'
    if os.path.exists(download_dir):
        for file in os.listdir(download_dir):
            file_path = os.path.join(download_dir, file)
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                    print(f"Removed file: {file_path}")
                except Exception as e:
                    print(f"Failed to remove {file_path}: {e}")
            elif os.path.isdir(file_path):
                try:
                    shutil.rmtree(file_path)
                    print(f"Removed directory: {file_path}")
                except Exception as e:
                    print(f"Failed to remove directory {file_path}: {e}")

if __name__ == "__main__":
    main()
