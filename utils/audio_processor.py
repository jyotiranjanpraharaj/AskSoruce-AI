import os
from pydub import AudioSegment

DOWNLOAD_DIR = 'downloades'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def clean_cookie_content(content: str) -> str:
    """Automatically clean up and convert space-separated cookies back to Tab-separated Netscape format."""
    cleaned_lines = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            cleaned_lines.append(line)
            continue
        # Split by any whitespace (tabs or multiple spaces)
        parts = stripped.split()
        if len(parts) >= 7:
            domain = parts[0]
            flag = parts[1]
            path = parts[2]
            secure = parts[3]
            expiration = parts[4]
            name = parts[5]
            value = " ".join(parts[6:])
            cleaned_lines.append(f"{domain}\t{flag}\t{path}\t{secure}\t{expiration}\t{name}\t{value}")
        else:
            cleaned_lines.append(line)
    return "\n".join(cleaned_lines)

def download_youtube_audio(url: str) -> str:
    """Download audio from YouTube using yt-dlp with pytubefix fallback."""
    print(f"Downloading audio from YouTube URL...")
    
    # Handle YOUTUBE_COOKIES environment variable or local cookies.txt file
    cookie_path = os.path.join(DOWNLOAD_DIR, "cookies.txt")
    env_cookies = os.getenv("YOUTUBE_COOKIES")
    
    if env_cookies:
        try:
            cleaned_cookies = clean_cookie_content(env_cookies)
            with open(cookie_path, "w", encoding="utf-8") as f:
                f.write(cleaned_cookies)
            print("Successfully loaded and formatted YouTube cookies from environment variable.")
        except Exception as ce:
            print(f"Failed to write environment cookies: {ce}")
    elif os.path.exists("cookies.txt"):
        # If user committed/uploaded cookies.txt to root
        cookie_path = "cookies.txt"
    else:
        cookie_path = None

    try:
        import yt_dlp
        out_template = os.path.join(DOWNLOAD_DIR, "%(id)s_%(title)s.%(ext)s")
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': out_template,
            'nocheckcertificate': True,
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {
                'youtube': {
                    'client': ['ios', 'android', 'mweb']
                }
            }
        }
        if cookie_path and os.path.exists(cookie_path):
            ydl_opts['cookiefile'] = cookie_path
            print("Passing cookies to yt-dlp configuration.")
            
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
            raise ValueError(
                "YouTube detected bot activity. To fix this, export a 'cookies.txt' file from your browser "
                "and set it as the YOUTUBE_COOKIES environment variable on Render, or place 'cookies.txt' "
                "in your project root."
            )

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