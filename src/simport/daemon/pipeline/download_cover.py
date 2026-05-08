import requests
import os
import logging
from tempfile import gettempdir

logger = logging.getLogger(__name__)

def download_cover(artist: str, title: str, album: str, output_dir: str) -> str | None:
    """
    Searches for the album cover using the iTunes Search API and downloads it.
    Returns the filename if successful, otherwise None.
    """
    
    # Try different search combinations in order of precision
    queries = []
    queries.append(f"{artist} {title}")
    
    logger.info(f"Looking for album cover for '{artist} - {title}' via iTunes API...")
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
                    logger.info(f"Found cover artwork. Using URL: {cover_url}")
                    break
        except Exception as e:
            logger.warning(f"Error while querying iTunes API: {e}")
            pass
            
    if not cover_url:
        logger.warning(f"Could not find any high-res cover for '{artist} - {title}'")
        return None
        
    try:
        # Download the image
        logger.info(f"Downloading cover image...")
        img_response = requests.get(cover_url, timeout=10)
        img_response.raise_for_status()
        
        output_file = os.path.join(output_dir, "cover.jpg")
        with open(output_file, 'wb') as f:
            f.write(img_response.content)
            
        logger.info(f"Cover successfully saved to {output_file}")
        return "cover.jpg"
    except Exception as e:
        logger.error(f"Failed to download/save cover image: {e}")
        return None