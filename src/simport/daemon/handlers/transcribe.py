import socketio
import asyncio
import logging
from typing import Dict, Any

from simport.cli.cli import get_client, take_first_result_with_synced_lyrics
from simport.daemon.utils import create_sync_emitter
from simport.daemon.pipeline.align_lyrics import AlignmentResult, align_lyrics
from simport.daemon.pipeline.remove_music import remove_music

logger = logging.getLogger(__name__)

def setup_transcribe_handlers(sio: socketio.AsyncServer):
    async def handle_transcribe(sid: str, data: Dict[str, Any]):
        lyrics_id = data.get('id')
        query = data.get('query')
        file_path = data.get('file')
        output_path = data.get('output')
        lang = data.get('lang', 'en')
        raw = data.get('raw', False)
        offset_fix = data.get('offset_fix', True)

        if not lyrics_id and not query:
            await sio.emit('transcribe:error', {'success': False, 'error': 'You must provide either id or query.'}, to=sid)
            return
        if not file_path or not output_path:
            await sio.emit('transcribe:error', {'success': False, 'error': 'You must provide both file and output paths.'}, to=sid)
            return

        loop = asyncio.get_running_loop()
        emit_progress = create_sync_emitter(sio, sid, loop, 'transcribe:progress')

        try:
            out_file = await loop.run_in_executor(None, _do_transcribe, lyrics_id, query, file_path, output_path, lang, raw, offset_fix, emit_progress)
            await sio.emit('transcribe:result', {'success': True, 'output': out_file}, to=sid)
        except Exception as e:
            logger.error(f"Transcribe API error: {e}", exc_info=True)
            await sio.emit('transcribe:error', {'success': False, 'error': str(e)}, to=sid)

    sio.on('transcribe', handle_transcribe)

def _do_transcribe(lyrics_id, query, file_path, output_path, lang, raw, offset_fix, emit_progress):
    client = get_client()
    lyrics = None

    if query:
        emit_progress({"step": "searching", "message": f"Searching for \"{query}\"..."})
        results = client.search_lyrics(q=query)
        if not results:
            raise Exception("No results found for the given query.")
        lyrics = take_first_result_with_synced_lyrics(results)
        if not lyrics:
            raise Exception("No results with synced lyrics found for the given query.")
    elif lyrics_id:
        emit_progress({"step": "searching", "message": f"Fetching lyrics for ID {lyrics_id}..."})
        lyrics = client.get_lyrics_by_id(lyrics_id)
        if not lyrics.id:
            raise Exception("No lyrics found with the given ID.")

    if not lyrics:
        raise Exception("No suitable lyrics found for alignment.")
    if not lyrics.syncedLyrics:
        raise Exception(f"The lyrics for '{lyrics.artistName} - {lyrics.trackName}' are not synced.")

    emit_progress({"step": "transcribing_init", "message": f"Transcribing {lyrics.artistName} - {lyrics.trackName}..."})

    if raw:
        result = AlignmentResult(lyrics.to_whisperx_segments())
    else:
        emit_progress({"step": "separating_audio", "message": "Removing music from audio..."})
        vocals_path = remove_music(file_path)

        emit_progress({"step": "transcribing", "message": "Transcribing audio (alignment)..."})
        result = align_lyrics(lyrics, vocals_path, language_code=lang, offset_fix=offset_fix)

    emit_progress({"step": "saving", "message": "Saving output file..."})
    
    output_lower = output_path.lower()
    if output_lower.endswith(".srt"):
        result.save_to_srt_file(output_path)
    elif output_lower.endswith(".vtt"):
        result.save_to_vtt_file(output_path)
    elif output_lower.endswith(".ass"):
        result.save_to_ass_file(output_path)
    elif output_lower.endswith(".txt"):
        result.save_to_ultrastar_file(output_path, artist=lyrics.artistName, title=lyrics.trackName, audio=output_path)
    else:
        raise Exception("Unsupported output format. Please use .srt, .vtt, .ass or .txt extension.")

    return output_path
