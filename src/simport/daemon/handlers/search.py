import socketio
import asyncio
import logging
from typing import Dict, Any

from simport.cli.cli import get_client

logger = logging.getLogger(__name__)

def setup_search_handlers(sio: socketio.AsyncServer):
    async def handle_search(sid: str, data: Dict[str, Any]):
        artist = data.get('artist')
        title = data.get('title')
        query = data.get('query')

        if not query and not title and not artist:
            await sio.emit('search:error', {'success': False, 'error': 'You must provide at least one of query, title, or artist.'}, to=sid)
            return

        try:
            loop = asyncio.get_running_loop()
            # Run the synchronous API call in an executor to avoid blocking the event loop
            results = await loop.run_in_executor(None, _do_search, query, title, artist)
            
            await sio.emit('search:result', {
                'success': True,
                'results': results
            }, to=sid)
        except Exception as e:
            logger.error(f"Search API error: {e}", exc_info=True)
            await sio.emit('search:error', {'success': False, 'error': str(e)}, to=sid)

    sio.on('search', handle_search)

def _do_search(query: str | None, title: str | None, artist: str | None):
    client = get_client()
    q_param = query if query else None
    track_name = title if title else (None if query else "")
    results = client.search_lyrics(q=q_param, track_name=track_name, artist_name=artist)
    
    if not results:
        return []
        
    return [
        {
            "id": result.id,
            "artistName": result.artistName,
            "trackName": result.trackName,
            "duration": result.duration
        }
        for result in results
    ]
