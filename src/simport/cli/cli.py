import os
import sys
from pathlib import Path
import click
import socketio

from simport.daemon.pipeline.lrclib_api import LRCLibClient

DAEMON_URL = os.environ.get("SIMPORT_DAEMON_URL", "http://127.0.0.1:8000")

def get_client() -> LRCLibClient:
    return LRCLibClient(
        app_name="vibes-ai-based-import",
        version="0.1.0",
        url="https://github.com/harrydehix/vibes-ai-based-import"
    )

def format_duration(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    return f"{m:02}:{s:02}"

def take_first_result_with_synced_lyrics(results):
    for result in results:
        if result.syncedLyrics:
            return result
    return None

def get_appdata_dir() -> Path:
    """Returns the platform-specific appdata directory for vibes."""
    home = Path.home()
    if os.name == 'nt':
        return Path(os.environ.get('APPDATA', home / 'AppData' / 'Roaming')) / 'vibes'
    elif sys.platform == 'darwin':
        return home / 'Library' / 'Application Support' / 'vibes'
    else:
        return home / '.local' / 'share' / 'vibes'

@click.group()
def cli():
    """AI based song import for vibes."""
    pass


@cli.command(name="search", help="Search for available lyrics on lrclib.net.")
@click.option("--artist", help="Artist Name")
@click.option("--title", help="Song Title")
@click.option("--query", help="Optional search query")
def search(artist: str, title: str, query: str):
    """Search for available lyrics via the Socket.IO Daemon."""
    if not query and not title and not artist:
        click.secho("Error: You must provide at least one of --query, --title, or --artist.", fg="red")
        return

    sio = socketio.SimpleClient()
    try:
        sio.connect(DAEMON_URL)
        sio.emit('search', {
            'artist': artist,
            'title': title,
            'query': query
        })
        
        while True:
            event = sio.receive()
            if event[0] == 'search:result':
                results = event[1].get('results', [])
                if not results:
                    click.secho("No results found.", fg="yellow")
                else:
                    for i, result in enumerate(results, start=1):
                        dur = format_duration(result.get('duration', 0))
                        click.secho(f"{i}) ", fg="cyan", nl=False)
                        click.secho(f"{result.get('artistName')} - {result.get('trackName')} ", fg="green", nl=False)
                        click.secho(f"({dur}) ", fg="yellow", nl=False)
                        click.secho(f"[ID: {result.get('id')}]", fg="blue")
                break
            elif event[0] == 'search:error':
                err = event[1].get('error')
                click.secho(f"Search Error: {err}", fg="red")
                break
            
    except Exception as e:
        click.secho(f"Connection to daemon failed. Is the daemon running?", fg="red")
    finally:
        if sio.connected:
            sio.disconnect()


@cli.command(name="transcribe", help="Transcribe a song and align its lyrics on word-level.")
@click.option("--id", "lyrics_id", type=int, help="lrclib.net ID of the song to transcribe")
@click.option("--query", help="Any query to search for the song")
@click.option("--file", required=True, type=click.Path(exists=True, dir_okay=False), help="Path to audio file")
@click.option("--output", required=True, type=click.Path(dir_okay=False, writable=True), help="Path to output file")
@click.option("--lang", default="en", help="Language for transcription (default: en)")
@click.option("--raw", is_flag=True, help="Skip alignment and just use the original timings from lrclib.net")
@click.option("--offset-fix/--no-offset-fix", default=True, help="Automatically fix offset")
def transcribe(lyrics_id: int, query: str, file: str, output: str, lang: str, raw: bool, offset_fix: bool):
    """Transcribe a song via the Socket.IO Daemon."""
    if not lyrics_id and not query:
        click.secho("Error: You must provide either --id or --query.", fg="red")
        return

    abs_file = str(Path(file).absolute())
    abs_output = str(Path(output).absolute())

    sio = socketio.SimpleClient()
    try:
        sio.connect(DAEMON_URL)
        sio.emit('transcribe', {
            'id': lyrics_id,
            'query': query,
            'file': abs_file,
            'output': abs_output,
            'lang': lang,
            'raw': raw,
            'offset_fix': offset_fix
        })
        
        while True:
            event = sio.receive()
            if event[0] == 'transcribe:progress':
                msg = event[1].get('message', '')
                click.secho(f"[{event[1].get('step')}] {msg}", fg="cyan")
            elif event[0] == 'transcribe:result':
                out_path = event[1].get('output')
                click.secho(f"Finished! Output saved to {out_path}", fg="green")
                break
            elif event[0] == 'transcribe:error':
                err = event[1].get('error')
                click.secho(f"Transcribe Error: {err}", fg="red")
                break

    except Exception as e:
        click.secho(f"Connection to daemon failed. Is the daemon running?", fg="red")
    finally:
        if sio.connected:
            sio.disconnect()


@cli.command(name="vimport")
@click.option("--youtube", required=True, help="YouTube video link")
@click.option("--output", required=False, help="Output directory")
@click.option("--raw", is_flag=True, help="Skip alignment and just use the original timings from lrclib.net")
@click.option("--lang", required=False, help="Language code")
@click.option("--infer-lang", is_flag=True, default=False, help="Automatically infer language")
@click.option("--offset-fix/--no-offset-fix", default=True, help="Automatically fix offset")
@click.option("--gemini-api-key", envvar="GEMINI_API_KEY", required=False, help="Google Gemini API key")
def vimport(youtube: str, output: str, raw: bool, lang: str | None, infer_lang: bool, offset_fix: bool, gemini_api_key: str | None):
    """Import a song via the Socket.IO Daemon."""
    sio = socketio.SimpleClient()
    
    if not output:
        # Fallback to appdata directory if no explicit output given to preserve old behaviour structure
        import uuid
        safe_title = f"youtube_import_{uuid.uuid4().hex[:8]}"
        output = str(get_appdata_dir() / 'songs' / safe_title)

    abs_output = str(Path(output).absolute())

    try:
        sio.connect(DAEMON_URL)
        sio.emit('vimport', {
            'youtube': youtube,
            'output': abs_output,
            'lang': lang,
            'infer_lang': infer_lang,
            'offset_fix': offset_fix,
            'gemini_api_key': gemini_api_key,
            'raw': raw
        })
        
        while True:
            event = sio.receive()
            if event[0] == 'vimport:progress':
                msg = event[1].get('message', '')
                click.secho(f"[{event[1].get('step')}] {msg}", fg="cyan")
            elif event[0] == 'vimport:result':
                out_path = event[1].get('output')
                click.secho(f"Finished! Output saved to {out_path}", fg="green")
                break
            elif event[0] == 'vimport:error':
                err = event[1].get('error')
                click.secho(f"VImport Error: {err}", fg="red")
                break

    except Exception as e:
        click.secho(f"Connection to daemon failed. Is the daemon running?", fg="red")
    finally:
        if sio.connected:
            sio.disconnect()


def main():
    cli()

@cli.command(name="daemon", help="Start the Socket.IO daemon for local API access.")
@click.option("--port", default=8000, help="Port to run the daemon on (default: 8000)")
@click.option("--host", default="127.0.0.1", help="Host to bind the daemon to (default: 127.0.0.1)")
def daemon(port: int, host: str):
    """Start the background daemon API."""
    from simport.logger import setup_logger
    setup_logger()
    
    from simport.daemon.server import start_server
    start_server(host=host, port=port)

if __name__ == '__main__':
    main()
