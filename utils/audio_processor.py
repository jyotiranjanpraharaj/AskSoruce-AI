import os
from pydub import AudioSegment

DOWNLOAD_DIR = 'downloades'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def download_youtube_audio(url: str) -> str:
    """Download audio from YouTube using yt-dlp with pytubefix fallback."""
    print(f"Downloading audio from YouTube URL...")
    try:
        import yt_dlp
        out_template = os.path.join(DOWNLOAD_DIR, "%(id)s_%(title)s.%(ext)s")
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': out_template,
            'nocheckcertificate': True,
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename
    except Exception as e:
        print(f"yt-dlp download failed: {e}. Trying pytubefix fallback...")
        try:
            from pytubefix import YouTube
            yt = YouTube(url)
            audio_stream = yt.streams.filter(only_audio=True).first()
            downloaded_file = audio_stream.download(output_path=DOWNLOAD_DIR)
            return downloaded_file
        except Exception as fallback_e:
            raise ValueError(f"Failed to download audio from YouTube: {fallback_e}")

def convert_to_mp3(input_path: str) -> str:
    """Convert any audio/video file to 16kHz mono MP3 format using pydub for compact size."""
    output_path = os.path.splitext(input_path)[0] + "_converted.mp3"
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(output_path, format="mp3", bitrate="64k")
    return output_path

def chunk_audio(mp3_path: str, chunk_minutes: int = 10) -> list:
    """Chunk compressed MP3 audio file into manageable segments."""
    audio = AudioSegment.from_file(mp3_path)
    chunk_ms = chunk_minutes * 60 * 1000 

    chunks = []
    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start : start + chunk_ms]
        chunk_path = f"{mp3_path}_chunk_{i}.mp3"
        chunk.export(chunk_path, format="mp3", bitrate="64k")
        chunks.append(chunk_path)
    
    return chunks

def process_input(source: str) -> list:
    if source.startswith("http://") or source.startswith("https://"):
        print("Detected YouTube URL. Downloading audio...")
        downloaded = download_youtube_audio(source)
        audio_path = convert_to_mp3(downloaded)
    else:
        print("Detected local file. Converting audio...")
        audio_path = convert_to_mp3(source)

    print("Chunking audio...")
    chunks = chunk_audio(audio_path)
    print(f"Audio ready — {len(chunks)} chunk(s) created.")
    return chunks