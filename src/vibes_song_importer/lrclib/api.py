import requests
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

class LRCLibError(Exception):
    """Exception raised for errors in the LRCLIB API."""
    def __init__(self, code: int, name: str, message: str):
        self.code = code
        self.name = name
        self.message = message
        super().__init__(f"[{code}] {name}: {message}")

@dataclass
class Lyrics:
    """Represents a lyrics entry from the LRCLIB API."""
    id: int
    trackName: str
    artistName: str
    albumName: str
    duration: int
    instrumental: bool
    plainLyrics: Optional[str]
    syncedLyrics: Optional[list[tuple[float, str]]]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Lyrics":

        raw_syncedLyrics=data.get("syncedLyrics")

        # format is `[00:17.12] I feel your breath upon my neck`
        syncedLyrics = []
        if isinstance(raw_syncedLyrics, str):
            for line in raw_syncedLyrics.splitlines():
                if line.startswith("[") and "]" in line:
                    try:
                        timestamp_str, lyric_line = line.split("]", 1)
                        timestamp_str = timestamp_str[1:]  # Remove the leading '['
                        minutes, seconds = map(float, timestamp_str.split(":"))
                        timestamp = minutes * 60 + seconds
                        syncedLyrics.append((timestamp, lyric_line.strip()))
                    except ValueError:
                        # If parsing fails, we can skip this line or handle it as needed
                        continue


        return cls(
            id=data.get("id", 0),
            trackName=data.get("trackName", ""),
            artistName=data.get("artistName", ""),
            albumName=data.get("albumName", ""),
            duration=data.get("duration", 0),
            instrumental=data.get("instrumental", False),
            plainLyrics=data.get("plainLyrics"),
            syncedLyrics=syncedLyrics
        )
    
    def to_whisperx_segments(self) -> list[dict]:
        """
        Converts the synced lyrics into a format suitable for WhisperX (list of dicts with 'text', 'start', 'end').
        If there are no synced lyrics, returns an empty list.
        """
        segments = []
        if not self.syncedLyrics:
            return segments

        for i, (start_time, text) in enumerate(self.syncedLyrics):
            if i < len(self.syncedLyrics) - 1:
                end_time = self.syncedLyrics[i + 1][0]
            else:
                end_time = float(self.duration)

            if text.strip() == "":
                continue

            segments.append({
                "text": text,
                "start": float(start_time),
                "end": float(end_time)
            })
            
        return segments

@dataclass
class CryptoChallenge:
    """Represents the cryptographic challenge for generating a publish token."""
    prefix: str
    target: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CryptoChallenge":
        return cls(
            prefix=data.get("prefix", ""),
            target=data.get("target", "")
        )

class LRCLibClient:
    """
    Python Client for the LRCLIB API (https://lrclib.net/api).
    """
    BASE_URL = "https://lrclib.net/api"

    def __init__(self, app_name: str, version: str, url: str):
        """
        Initializes the client with the recommended User-Agent header.
        Example: LRCLibClient("MyMusicPlayer", "1.0", "https://github.com/user/repo")
        """
        self.session = requests.Session()
        # According to the documentation, the User-Agent is highly recommended.
        self.session.headers.update({
            "User-Agent": f"{app_name} v{version} ({url})"
        })

    def _handle_response(self, response: requests.Response) -> Any:
        """Helper function to evaluate the HTTP response and handle errors."""
        try:
            data = response.json()
        except requests.exceptions.JSONDecodeError:
            data = {}
        
        if response.status_code >= 400:
            if isinstance(data, dict) and "message" in data:
                raise LRCLibError(
                    code=data.get("code", response.status_code),
                    name=data.get("name", "UnknownError"),
                    message=data.get("message", "An unknown error occurred.")
                )
            response.raise_for_status()

        return data

    def get_lyrics(self, track_name: str, artist_name: str, album_name: str, duration: int) -> Lyrics:
        """
        Attempts to find the best lyrics for the track (including external sources).
        """
        params = {
            "track_name": track_name,
            "artist_name": artist_name,
            "album_name": album_name,
            "duration": duration
        }
        response = self.session.get(f"{self.BASE_URL}/get", params=params)
        return Lyrics.from_dict(self._handle_response(response))

    def get_cached_lyrics(self, track_name: str, artist_name: str, album_name: str, duration: int) -> Lyrics:
        """
        Searches for lyrics ONLY in the internal database (no external requests, therefore faster).
        """
        params = {
            "track_name": track_name,
            "artist_name": artist_name,
            "album_name": album_name,
            "duration": duration
        }
        response = self.session.get(f"{self.BASE_URL}/get-cached", params=params)
        return Lyrics.from_dict(self._handle_response(response))

    def get_lyrics_by_id(self, lyrics_id: int) -> Lyrics:
        """
        Retrieves a specific lyrics entry by its LRCLIB ID.
        """
        response = self.session.get(f"{self.BASE_URL}/get/{lyrics_id}")
        return Lyrics.from_dict(self._handle_response(response))

    def search_lyrics(self, 
                      q: Optional[str] = None, 
                      track_name: Optional[str] = None, 
                      artist_name: Optional[str] = None, 
                      album_name: Optional[str] = None) -> List[Lyrics]:
        """
        Searches for lyrics. According to the docs, at least 'q' or 'track_name' MUST be provided.
        Returns a maximum of 20 results.
        """
        if not q and not track_name:
            raise ValueError("At least 'q' or 'track_name' must be provided.")

        params = {}
        if q: params["q"] = q
        if track_name: params["track_name"] = track_name
        if artist_name: params["artist_name"] = artist_name
        if album_name: params["album_name"] = album_name

        response = self.session.get(f"{self.BASE_URL}/search", params=params)
        data = self._handle_response(response)
        
        if isinstance(data, list):
            return [Lyrics.from_dict(item) for item in data]
        return []

    def request_challenge(self) -> CryptoChallenge:
        """
        Generates a prefix and a target for the cryptographic Proof-of-Work puzzle.
        (Required to generate a Publish-Token).
        """
        response = self.session.post(f"{self.BASE_URL}/request-challenge")
        return CryptoChallenge.from_dict(self._handle_response(response))

    def publish_lyrics(self, 
                       publish_token: str, 
                       track_name: str, 
                       artist_name: str, 
                       album_name: str, 
                       duration: int, 
                       plain_lyrics: str = "", 
                       synced_lyrics: str = "") -> None:
        """
        Publishes new lyrics. 
        If plain_lyrics AND synced_lyrics are empty, the track is marked as instrumental.
        'publish_token' must be in the format {prefix}:{nonce}, calculated from request_challenge().
        """
        headers = {
            "X-Publish-Token": publish_token
        }
        payload = {
            "trackName": track_name,
            "artistName": artist_name,
            "albumName": album_name,
            "duration": duration,
            "plainLyrics": plain_lyrics,
            "syncedLyrics": synced_lyrics
        }
        
        response = self.session.post(f"{self.BASE_URL}/publish", headers=headers, json=payload)
        self._handle_response(response)
        return None


