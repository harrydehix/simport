import yt_dlp
import os
from tempfile import gettempdir

def download_youtube_video_and_audio(url: str, output_dir: str):
    """
    Downloads the video and audio from a YouTube link.
    Extracts the audio to a separate mp3 file and keeps the video as mp4.
    Returns a dictionary with paths to video, audio and the video title.
    """
    
    # Path setup
    video_path = os.path.join(output_dir, "video.mp4")
    audio_path = os.path.join(output_dir, "audio.mp3")
    
    from typing import Any
    ydl_opts: Any = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
        'outtmpl': {'default': video_path},
        'quiet': True,
        'no_warnings': True,
        'keepvideo': True, 
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }
        ]
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        video_title = info_dict.get('title', 'Unknown Title')
        
    extracted_audio = os.path.splitext(video_path)[0] + ".mp3"
    if os.path.exists(extracted_audio):
        if os.path.exists(audio_path):
            os.remove(audio_path)
        os.rename(extracted_audio, audio_path)
        
    return {
        "title": video_title,
        "video": video_path,
        "audio": audio_path
    }
