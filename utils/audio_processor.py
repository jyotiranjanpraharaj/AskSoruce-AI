import os
import socket
import urllib3
urllib3.util.connection.allowed_gai_family = lambda: socket.AF_INET
from pydub import AudioSegment

DOWNLOAD_DIR = 'downloades'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def download_via_rapidapi(video_id: str) -> str:
    """Download audio from YouTube using RapidAPI's YouTube MP3 Audio Video Downloader."""
    import requests
    
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        raise ValueError("RAPIDAPI_KEY environment variable is not set.")
        
    url = f"https://youtube-mp3-audio-video-downloader.p.rapidapi.com/get_raw_audio_download_link/{video_id}"
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "youtube-mp3-audio-video-downloader.p.rapidapi.com"
    }
    querystring = {"quality": "140"}
    
    print(f"Calling RapidAPI to get audio link for video {video_id}...")
    response = requests.get(url, headers=headers, params=querystring, timeout=10)
    
    if response.status_code != 200:
        raise ValueError(f"RapidAPI request failed with status code {response.status_code}: {response.text}")
        
    data = response.json()
    # Check multiple common keys in the JSON payload defensively
    download_url = data.get("url") or data.get("download_link") or data.get("downloadUrl")
    if not download_url and isinstance(data.get("result"), dict):
        download_url = data.get("result").get("url") or data.get("result").get("download_link")
        
    if not download_url:
        # Check nested structures
        if isinstance(data.get("download"), dict):
            download_url = data.get("download").get("url") or data.get("download").get("download_link")
        
    if not download_url:
        # Fallback to checking the whole response for any URL string
        for k, v in data.items():
            if isinstance(v, str) and v.startswith("http"):
                download_url = v
                break
                
    if not download_url:
        raise ValueError(f"Failed to find download URL in RapidAPI response: {data}")
        
    print(f"RapidAPI Success! Downloading audio file from: {download_url}")
    
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.m4a")
    
    # Download the actual file from the direct link
    res = requests.get(download_url, stream=True, timeout=30)
    if res.status_code == 200:
        with open(file_path, "wb") as f:
            for chunk in res.iter_content(chunk_size=8192):
                f.write(chunk)
        return file_path
        
    raise ValueError(f"Failed to download audio file from RapidAPI link (Status: {res.status_code})")

def download_via_cobalt(youtube_url: str) -> str:
    """Download audio from YouTube using public Cobalt instances as a fallback."""
    print("Attempting to download via public Cobalt instances...")
    import requests
    import re
    
    instances = []
    try:
        res = requests.get("https://cobalt.directory", timeout=5)
        if res.status_code == 200:
            urls = re.findall(r'https://[a-zA-Z0-9.-]*cobalt[a-zA-Z0-9.-]*\.[a-zA-Z]{2,}', res.text)
            for url in set(urls):
                url = url.strip()
                if "directory" not in url and "tools" not in url:
                    instances.append(url)
            print(f"Dynamically discovered {len(instances)} active Cobalt mirrors from tracker.")
    except Exception as ie:
        print(f"Failed to scrape cobalt.directory: {ie}")
        
    # If scraping fails, use the verified, current active mirrors list
    if not instances:
        instances = [
            "https://cobalt.tame.gg",
            "https://cobalt.eversiege.network",
            "https://cobalt.clxxped.lol",
            "https://cobalt.kittycat.boo",
            "https://cobalt.liubquanti.click",
            "https://cobalt.squair.xyz",
            "https://cobalt.meowing.de",
            "https://cobalt.xenon.zone",
            "https://cobalt.cjs.nz"
        ]

    for base_url in instances:
        if not base_url:
            continue
            
        # Try both the newer API endpoint (POST /) and older (POST /api/json)
        for api_path in ["", "/api/json"]:
            api_url = base_url.rstrip("/") + api_path
            print(f"Trying Cobalt instance: {api_url}")
            try:
                payload = {
                    "url": youtube_url,
                    "downloadMode": "audio",
                    "audioFormat": "mp3",
                    "filenamePattern": "basic"
                }
                headers = {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                }
                
                post_res = requests.post(api_url, json=payload, headers=headers, timeout=10)
                if post_res.status_code != 200:
                    continue
                    
                data = post_res.json()
                download_url = data.get("url")
                if not download_url:
                    continue
                    
                print(f"Success! Downloading audio file from Cobalt mirror: {download_url}")
                
                # Fetch filename or generate one
                filename_clean = re.sub(r'[^a-zA-Z0-9]', '_', youtube_url.split("v=")[-1]) + ".mp3"
                file_path = os.path.join(DOWNLOAD_DIR, filename_clean)
                
                # Download the actual file
                file_res = requests.get(download_url, stream=True, timeout=30)
                if file_res.status_code == 200:
                    with open(file_path, "wb") as f:
                        for chunk in file_res.iter_content(chunk_size=8192):
                            f.write(chunk)
                    return file_path
            except Exception as inst_e:
                print(f"Instance {api_url} failed: {inst_e}")
                continue
                
    raise ValueError("All Cobalt download instances failed or timed out.")

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
    """Download audio from YouTube using RapidAPI, yt-dlp, or Cobalt fallbacks."""
    print(f"Downloading audio from YouTube URL...")
    import re
    
    # Extract video ID from URL
    video_id = None
    patterns = [
        r'(?:v=|\/)([a-zA-Z0-9_-]{11})',
        r'youtu\.be\/([a-zA-Z0-9_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            break
            
    # Try RapidAPI first if key is configured
    if video_id and os.getenv("RAPIDAPI_KEY"):
        try:
            print("RapidAPI Key detected. Attempting to download via RapidAPI...")
            file_path = download_via_rapidapi(video_id)
            return file_path
        except Exception as ra_e:
            print(f"RapidAPI download failed: {ra_e}. Falling back to local/Cobalt engines...")
            
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
            print(f"pytubefix download failed: {fallback_e}. Trying Cobalt API fallback...")
            try:
                downloaded_file = download_via_cobalt(url)
                return downloaded_file
            except Exception as cobalt_e:
                raise ValueError(
                    f"YouTube download failed completely. Reason: {cobalt_e}. "
                    "To fix this, export a fresh 'cookies.txt' file from your browser "
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