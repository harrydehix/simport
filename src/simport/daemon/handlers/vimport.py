import socketio
import asyncio
import logging
import yt_dlp
from pathlib import Path
from typing import Dict, Any

from simport.cli.cli import get_client, take_first_result_with_synced_lyrics
from simport.daemon.utils import create_sync_emitter
from simport.daemon.pipeline.align_lyrics import AlignmentResult, align_lyrics
from simport.daemon.pipeline.remove_music import remove_music
from simport.daemon.pipeline.download_youtube_video_and_audio import download_youtube_video_and_audio
from simport.daemon.pipeline.download_cover import download_cover

logger = logging.getLogger(__name__)

def setup_vimport_handlers(sio: socketio.AsyncServer):
    async def handle_vimport(sid: str, data: Dict[str, Any]):
        youtube_url = data.get('youtube')
        output_dir = data.get('output')
        lang = data.get('lang')
        infer_lang = data.get('infer_lang', False)
        offset_fix = data.get('offset_fix', True)
        gemini_api_key = data.get('gemini_api_key')
        raw = data.get('raw', False)

        if not youtube_url or not output_dir:
            await sio.emit('vimport:error', {'success': False, 'error': 'You must provide both youtube and output parameters.'}, to=sid)
            return

        loop = asyncio.get_running_loop()
        emit_progress = create_sync_emitter(sio, sid, loop, 'vimport:progress')

        try:
            out_file = await loop.run_in_executor(None, _do_vimport, emit_progress, youtube_url, output_dir, lang, infer_lang, offset_fix, gemini_api_key, raw)
            await sio.emit('vimport:result', {'success': True, 'output': out_file}, to=sid)
        except Exception as e:
            logger.error(f"VImport API error: {e}", exc_info=True)
            await sio.emit('vimport:error', {'success': False, 'error': str(e)}, to=sid)

    sio.on('vimport', handle_vimport)

def _do_vimport(emit_progress, youtube: str, output_dir: str, lang: str | None, infer_lang: bool = False, offset_fix: bool = True, gemini_api_key: str | None = None, raw: bool = False):
    client = get_client()

    emit_progress({"step": "extracting_info", "message": f"Extracting video information for {youtube}..."})
    ydl_opts: Any = {'quiet': True, 'skip_download': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube, download=False)
        video_title = info.get('title')

    if not video_title:
        raise Exception("Could not extract video title from YouTube link.")

    if gemini_api_key:
        emit_progress({"step": "analyzing_title", "message": "Extracting song info from video title using Gemini API..."})
        from simport.daemon.pipeline.get_song_info_from_title import get_song_info_from_title
        try:
            song_info = get_song_info_from_title(video_title, api_key=gemini_api_key)
            if song_info:
                video_title = f"{song_info.interpret} - {song_info.song_name}"
                if infer_lang and not lang and song_info.language_code:
                    lang = song_info.language_code
        except Exception as e:
            logger.warning(f"Failed to infer from gemini: {e}")

    emit_progress({"step": "searching", "message": f"Searching for \"{video_title}\"..."})
    results = client.search_lyrics(q=video_title)
    if not results:
        raise Exception("No results found for the given query.")

    lyrics = take_first_result_with_synced_lyrics(results)
    if not lyrics:
        raise Exception("No results with synced lyrics found for the given query.")

    if not lyrics.syncedLyrics:
        raise Exception(f"The lyrics for '{lyrics.artistName} - {lyrics.trackName}' are not synced.")

    output_path = Path(output_dir) / f"{lyrics.artistName} - {lyrics.trackName}"
    output_path.mkdir(parents=True, exist_ok=True)
    output_txt = output_path / "song.txt"

    emit_progress({"step": "downloading_video", "message": "Downloading video and audio from YouTube..."})
    yt_result = download_youtube_video_and_audio(youtube, str(output_path))
    audio_file = yt_result['audio']

    emit_progress({"step": "downloading_cover", "message": "Downloading album cover..."})
    cover_filename = download_cover(
        artist=lyrics.artistName,
        title=lyrics.trackName,
        album=lyrics.albumName,
        output_dir=str(output_path)
    )

    if raw:
        result = AlignmentResult(lyrics.to_whisperx_segments())
    else:
        emit_progress({"step": "separating_audio", "message": "Removing music from audio..."})
        vocals_path = remove_music(audio_file)

        emit_progress({"step": "transcribing", "message": "Transcribing audio (alignment)..."})
        result = align_lyrics(lyrics, vocals_path, language_code=lang if lang else "en", offset_fix=offset_fix)

    emit_progress({"step": "saving", "message": "Saving output file..."})
    result.save_to_ultrastar_file(str(output_txt), artist=lyrics.artistName, title=lyrics.trackName, audio="audio.mp3", video="video.mp4", cover=cover_filename)

    return str(output_txt)
