import os
import socket
import urllib3
urllib3.util.connection.allowed_gai_family = lambda: socket.AF_INET
from pydub import AudioSegment

DOWNLOAD_DIR = 'downloades'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def download_via_rapidapi(video_id: str) -> str:
    """Download audio from YouTube using RapidAPI's YouTube MP3 Audio Video Downloader with polling."""
    import requests
    import time
    
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        raise ValueError("RAPIDAPI_KEY environment variable is not set.")
        
    url = f"https://youtube-mp3-audio-video-downloader.p.rapidapi.com/get_mp3_download_link/{video_id}"
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "youtube-mp3-audio-video-downloader.p.rapidapi.com"
    }
    querystring = {"quality": "low", "wait_until_the_file_is_ready": "false"}
    
    max_retries = 20  # Try for up to ~60-80 seconds
    for attempt in range(max_retries):
        print(f"Calling RapidAPI to get audio link for video {video_id} (Attempt {attempt + 1}/{max_retries})...")
        try:
            # Set timeout to 10s per request to avoid hanging
            response = requests.get(url, headers=headers, params=querystring, timeout=10)
            
            # If rate-limited or server error, wait and retry
            if response.status_code in [429, 500, 502, 503, 504]:
                print(f"RapidAPI returned temporary status code {response.status_code}. Retrying in 3 seconds...")
                time.sleep(3)
                continue
                
            if response.status_code != 200:
                raise ValueError(f"RapidAPI request failed with status code {response.status_code}: {response.text}")
                
            data = response.json()
        except (requests.RequestException, ValueError) as err:
            # Catch timeouts, connection errors, and JSON decode issues to retry
            print(f"RapidAPI attempt {attempt + 1} failed: {err}. Retrying in 3 seconds...")
            time.sleep(3)
            continue
            
        # Check multiple common keys in the JSON payload defensively
        download_url = data.get("url") or data.get("download_link") or data.get("downloadUrl")
        if not download_url and isinstance(data.get("result"), dict):
            download_url = data.get("result").get("url") or data.get("result").get("download_link")
            
        if not download_url and isinstance(data.get("download"), dict):
            download_url = data.get("download").get("url") or data.get("download").get("download_link")
            
        if not download_url:
            # Fallback to checking the whole response for any URL string
            for k, v in data.items():
                if isinstance(v, str) and v.startswith("http"):
                    download_url = v
                    break
                    
        # If we got the URL, proceed to download the audio file
        if download_url:
            print(f"RapidAPI Success! Downloading audio file from: {download_url}")
            file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.m4a")
            
            try:
                res = requests.get(download_url, stream=True, timeout=30)
                if res.status_code == 200:
                    with open(file_path, "wb") as f:
                        for chunk in res.iter_content(chunk_size=8192):
                            f.write(chunk)
                    return file_path
                print(f"Failed to download audio file from RapidAPI link (Status: {res.status_code}). Retrying...")
            except requests.RequestException as dl_err:
                print(f"Download stream error: {dl_err}. Retrying...")
            
        # If we didn't get the URL, the file is still converting. Sleep and retry.
        status_msg = data.get("status") or data.get("message") or "processing"
        print(f"Audio is still converting on API servers (Status: {status_msg}). Waiting 3 seconds...")
        time.sleep(3)
        
    raise ValueError("RapidAPI audio conversion timed out or failed after multiple retries.")

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
        
        # Check for PO Token and Visitor Data in the environment
        po_token = os.getenv("YOUTUBE_PO_TOKEN")
        visitor_data = os.getenv("YOUTUBE_VISITOR_DATA")
        
        youtube_args = {
            'client': ['ios', 'android', 'mweb']
        }
        if po_token:
            youtube_args['po_token'] = po_token
            # PO Tokens are usually web-client specific, so we target the web client
            youtube_args['player_client'] = 'web'
        if visitor_data:
            youtube_args['visitor_data'] = visitor_data

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': out_template,
            'nocheckcertificate': True,
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {
                'youtube': youtube_args
            },
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '64',
            }],
            'postprocessor_args': {
                'FFmpegExtractAudio': ['-ar', '16000', '-ac', '1']
            }
        }
        
        if cookie_path and os.path.exists(cookie_path):
            ydl_opts['cookiefile'] = cookie_path
            print("Passing cookies to yt-dlp configuration.")
            
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Find the actual downloaded and post-processed file path
            if 'requested_downloads' in info and len(info['requested_downloads']) > 0:
                filename = info['requested_downloads'][0].get('filepath')
            else:
                filename = ydl.prepare_filename(info)
                # If FFmpeg postprocessor converted it to .mp3, extension will have changed
                if not os.path.exists(filename):
                    base, _ = os.path.splitext(filename)
                    if os.path.exists(base + ".mp3"):
                        filename = base + ".mp3"
            
            print(f"yt-dlp successfully downloaded and converted audio: {filename}")
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
    """Convert any audio/video file to 16kHz mono MP3 format using FFmpeg subprocess for high speed and low memory."""
    import subprocess
    output_path = os.path.splitext(input_path)[0] + "_converted.mp3"
    print(f"Converting {input_path} to MP3 (16kHz, mono, 64kbps) via FFmpeg...")
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vn",
        "-acodec", "libmp3lame",
        "-ar", "16000",
        "-ac", "1",
        "-b:a", "64k",
        output_path
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return output_path
    except subprocess.CalledProcessError as e:
        raise ValueError(f"FFmpeg conversion failed: {e}")

def chunk_audio(mp3_path: str, chunk_minutes: int = 10) -> list:
    """Chunk compressed MP3 audio file into manageable segments using FFmpeg's segment muxer."""
    import subprocess
    import glob
    
    base_no_ext, ext = os.path.splitext(mp3_path)
    chunk_pattern = f"{base_no_ext}_chunk_%03d{ext}"
    chunk_time_secs = chunk_minutes * 60
    
    print(f"Segmenting audio file {mp3_path} into {chunk_minutes}-minute chunks via FFmpeg...")
    
    cmd = [
        "ffmpeg", "-y",
        "-i", mp3_path,
        "-f", "segment",
        "-segment_time", str(chunk_time_secs),
        "-c:a", "libmp3lame",
        "-ar", "16000",
        "-ac", "1",
        "-b:a", "64k",
        chunk_pattern
    ]
    
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        # Glob for files matching the output pattern
        glob_pattern = f"{base_no_ext}_chunk_[0-9][0-9][0-9]{ext}"
        chunks = sorted(glob.glob(glob_pattern))
        return chunks
    except subprocess.CalledProcessError as e:
        raise ValueError(f"FFmpeg segmenting failed: {e}")

def process_input(source: str) -> list:
    if source.startswith("http://") or source.startswith("https://"):
        print("Detected YouTube URL. Downloading audio...")
        downloaded = download_youtube_audio(source)
        # If the downloaded file is already the target MP3 format, skip conversion
        if downloaded.endswith("_converted.mp3") or downloaded.endswith(".mp3"):
            audio_path = downloaded
        else:
            audio_path = convert_to_mp3(downloaded)
    else:
        print("Detected local file. Converting audio...")
        audio_path = convert_to_mp3(source)

    print("Chunking audio...")
    chunks = chunk_audio(audio_path)
    print(f"Audio ready — {len(chunks)} chunk(s) created.")
    return chunks