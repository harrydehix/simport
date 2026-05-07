from attr import dataclass
from transformers import pipeline

from google import genai



@dataclass
class SongInfo:
    interpret: str
    song_name: str
    language_code: str

def get_song_info_from_title(title: str, api_key: str) -> SongInfo | None:
    client = genai.Client(api_key=api_key)
    result = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=f"""
        You extract the artist, song name and language code (de, en, fr, es, etc.) from a YouTube video title.
        Remove extra text like '(Official Video)', (feat. <name>), (visualizer), '[Lyrics]', '4K', ' x ' etc.
        Output ONLY the artist and song in this format exactly:
        Artist: <name>\nSong: <name>\nLanguage Code: <code>

        User: `{title}`
        """
    )
    response = result.text.strip()
    
    artist, song, language_code = None, None, None
    for line in response.splitlines():
        if line.lower().startswith("artist:"):
            artist = line.split(":", 1)[1].strip()
        elif line.lower().startswith("song:"):
            song = line.split(":", 1)[1].strip()
        elif line.lower().startswith("language code:"):
            language_code = line.split(":", 1)[1].strip()
            
    if artist and song:
        return SongInfo(interpret=artist, song_name=song, language_code=language_code)
    return None