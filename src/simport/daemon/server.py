import logging
import socketio
from aiohttp import web
import os
from pathlib import Path

from simport.logger import setup_logger
from simport.daemon.handlers.search import setup_search_handlers
from simport.daemon.handlers.transcribe import setup_transcribe_handlers
from simport.daemon.handlers.vimport import setup_vimport_handlers

logger = logging.getLogger(__name__)

async def index(request):
    return web.Response(text="vibes-ai-based-import daemon is running", content_type='text/html')

def create_app() -> web.Application:
    # Configure FFmpeg path
    confiugre_ffmpeg()

    # Create Socket.IO server
    sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins='*')
    
    # Register handlers
    setup_search_handlers(sio)
    setup_transcribe_handlers(sio)
    setup_vimport_handlers(sio)

    # Attach to aiohttp app
    app = web.Application()
    sio.attach(app)
    app.router.add_get('/', index)

    return app

def start_server(host: str = '127.0.0.1', port: int = 8000):
    """
    Start the Socket.IO daemon via aiohttp.
    """
    setup_logger()
    app = create_app()
    logger.info(f"Starting simport daemon on {host}:{port}")
    web.run_app(app, host=host, port=port)

def confiugre_ffmpeg():
    # Set up specific FFmpeg installation path based on the OS
    home = Path.home()
    ffmpeg_bin = None
    os.environ["TORCHAUDIO_USE_FFMPEG_VERSION"] = "7"
    os.environ["TORIO_USE_FFMPEG_VERSION "] = "7"
    if os.name == 'nt' or sys.platform == 'darwin':  # Windows or macOS
        # AppData / vibe location (when installed in production)
        appdata_base = Path(os.environ.get('APPDATA', home / 'AppData' / 'Roaming')) if os.name == 'nt' else home / 'Library' / 'Application Support'
        appdata_ffmpeg = appdata_base / 'vibes' / 'ffmpeg' / 'bin'
        
        # Local dev location
        local_ffmpeg = Path(__file__).parent.parent.parent.parent.parent / "ffmpeg" / "bin"
        
        if appdata_ffmpeg.exists():
            ffmpeg_bin = str(appdata_ffmpeg)
        elif local_ffmpeg.exists():
            ffmpeg_bin = str(local_ffmpeg)
    else: # linux
        ffmpeg_bin = "ffmpeg"

    if ffmpeg_bin and os.path.exists(ffmpeg_bin):
        os.environ["PATH"] = ffmpeg_bin + os.pathsep + os.environ.get("PATH", "")
        if hasattr(os, 'add_dll_directory'):
            try:
                os.add_dll_directory(ffmpeg_bin)
            except Exception:
                pass

    if ffmpeg_bin is None:
        raise Exception("FFmpeg binary not found. Please ensure FFmpeg is installed and available in the PATH.")

if __name__ == '__main__':
    start_server()
