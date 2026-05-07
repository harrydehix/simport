import requests
import os
from tempfile import gettempdir

def download_cover(artist: str, title: str, album: str, output_dir: str) -> str | None:
    """
    Searches for the album cover using the iTunes Search API and downloads it.
    Returns the filename if successful, otherwise None.
    """
    
    # Try different search combinations in order of precision
    queries = []
    queries.append(f"{artist} {title}")
    
    cover_url = None
    
    for query in queries:
        try:
            url = "https://itunes.apple.com/search"
            params = {
                "term": query,
                "media": "music",
                "entity": "song",
                "limit": 1
            }
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            if data.get("resultCount", 0) > 0:
                result = data["results"][0]
                artwork_url = result.get("artworkUrl100")
                if artwork_url:
                    # Upgrade the resolution from 100x100 to 1000x1000
                    cover_url = artwork_url.replace("100x100bb", "1000x1000bb")
                    break
        except Exception:
            pass
            
    if not cover_url:
        return None
        
    try:
        # Download the image
        img_response = requests.get(cover_url, timeout=10)
        img_response.raise_for_status()
        
        output_file = os.path.join(output_dir, "cover.jpg")
        with open(output_file, 'wb') as f:
            f.write(img_response.content)
            
        return "cover.jpg"
    except Exception:
        return None