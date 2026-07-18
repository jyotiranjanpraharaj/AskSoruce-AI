from groq import Groq
import os

def transcribe_chunk_whisper(chunk_path: str, language: str = None) -> str:
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise RuntimeError("GROQ_API_KEY is not set in environment / .env")

    client = Groq(api_key=groq_api_key)

    with open(chunk_path, "rb") as file:
        kwargs = {
            "file": (os.path.basename(chunk_path), file.read()),
            "model": "whisper-large-v3",
            "response_format": "json",
        }

        if language:
            lang_lower = language.lower()
            if lang_lower in ["hindi", "hi"]:
                kwargs["language"] = "hi"
            elif lang_lower in ["english", "en"]:
                kwargs["language"] = "en"
            elif lang_lower in ["hinglish"]:
                kwargs["language"] = "hi"

        transcription = client.audio.transcriptions.create(**kwargs)
    return transcription.text  


def transcribe_chunk(chunk_path: str, language: str = "english") -> str:
    """
    Route one chunk to Groq's Whisper transcriber.
    """
    return transcribe_chunk_whisper(chunk_path, language=language)


def transcribe_all(chunks: list, language: str = "english") -> str:
    full_transcript = "" 

    print("Using Groq Whisper for transcription.")

    for i, chunk in enumerate(chunks):  
        print(f"Transcribing chunk {i + 1}/{len(chunks)}...")
        text = transcribe_chunk(chunk, language=language)  
        full_transcript += text + " "  

    print("Transcription complete.")
    return full_transcript.strip()