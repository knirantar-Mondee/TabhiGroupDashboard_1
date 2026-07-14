import os
import requests

TEMP_MEDIA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "temp_media")
os.makedirs(TEMP_MEDIA_DIR, exist_ok=True)

def download_file(url, extension):
    """Downloads a file to a temp location and returns the filepath."""
    if not url:
        return None
    try:
        filename = f"temp_download_{hash(url)}.{extension}"
        filepath = os.path.join(TEMP_MEDIA_DIR, filename)
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(response.content)
            return filepath
    except Exception as e:
        print(f"⚠️ Failed to download media: {str(e)}")
    return None

def extract_text_from_image(image_url):
    """Downloads an image and performs OCR using easyocr."""
    if not image_url:
        return ""
    
    try:
        import easyocr
    except ImportError:
        return "[easyocr not installed. Run 'pip install easyocr torch torchvision']"
    
    filepath = download_file(image_url, "jpg")
    if not filepath:
        return "[Error downloading image]"
        
    try:
        reader = easyocr.Reader(['en'], gpu=False)
        results = reader.readtext(filepath, detail=0)
        text = " ".join(results).strip()
        return text if text else "[No text detected in image]"
    except Exception as e:
        return f"[OCR Error: {str(e)}]"
    finally:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)

def transcribe_video(video_url):
    """Downloads a video and transcribes its audio using faster-whisper."""
    if not video_url:
        return ""
        
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return "[faster-whisper not installed. Run 'pip install faster-whisper']"
        
    filepath = download_file(video_url, "mp4")
    if not filepath:
        return "[Error downloading video]"
        
    try:
        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, info = model.transcribe(filepath, beam_size=5)
        text = " ".join([segment.text for segment in segments]).strip()
        return text if text else "[No speech detected in video]"
    except Exception as e:
        return f"[Transcription Error: {str(e)}]"
    finally:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)

def get_youtube_transcript(video_url):
    """Retrieves subtitles/transcript directly from YouTube servers for free."""
    if not video_url:
        return ""
    
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        return "[youtube-transcript-api not installed. Run 'pip install youtube-transcript-api']"
        
    try:
        video_id = None
        if "v=" in video_url:
            video_id = video_url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in video_url:
            video_id = video_url.split("youtu.be/")[1].split("?")[0]
        elif "shorts/" in video_url:
            video_id = video_url.split("shorts/")[1].split("?")[0]
            
        if not video_id:
            return "[Could not parse Video ID]"
            
        transcript_obj = YouTubeTranscriptApi().fetch(video_id)
        transcript_text = " ".join([snippet.text for snippet in transcript_obj.snippets])
        return transcript_text.strip()
    except Exception as e:
        return f"[Transcript unavailable: {str(e)}]"
