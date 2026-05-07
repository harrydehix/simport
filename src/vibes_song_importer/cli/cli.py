import os
import sys
from pathlib import Path
import json as js

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
    print("FFmpeg binary not found. Please ensure FFmpeg is installed and available in the PATH.")
    sys.exit()

import click
from vibes_song_importer.lrclib.api import LRCLibClient
from vibes_song_importer.lyrics_alignment.alignment import AlignmentResult, align
from vibes_song_importer.lyrics_alignment.remove_music import remove_music
from vibes_song_importer.youtube.downloader import download_youtube_video_and_audio
from vibes_song_importer.cover.downloader import download_cover

def get_client() -> LRCLibClient:
    return LRCLibClient(
        app_name="vibes-ai-based-import",
        version="0.1.0",
        url="https://github.com/harrydehix/vibes-ai-based-import"
    )

def format_duration(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    return f"{m:02}:{s:02}"


@click.group()
def cli():
    """AI based song import for vibes."""
    pass


@cli.command(name="search", help="Search for available lyrics on LRCLIB.")
@click.option("--artist", help="Artist Name")
@click.option("--title", help="Song Title")
@click.option("--query", help="Optional search query")
@click.option("--json", is_flag=True, help="Output results in JSON format")
def search(artist: str, title: str, query: str, json: bool):
    """Search for available lyrics on LRCLIB."""
    if not query and not title and not artist:
        click.secho("Error: You must provide at least one of --query, --title, or --artist.", fg="red")
        return

    client = get_client()
    try:
        # LRCLib API requires at least q or track_name
        q_param = query if query else None
        track_name = title if title else (None if query else "")

        results = client.search_lyrics(
            q=q_param,
            track_name=track_name,
            artist_name=artist
        )

        if not results:
            if json:
                output = {
                    "success": True,
                    "results": []
                }
                click.echo(js.dumps(output, indent=4))
            else: 
                click.secho("No results found.", fg="yellow")
            return
        


        if json:
            output = {
                "success": True,
                "results": [
                    {
                        "id": result.id,
                        "artistName": result.artistName,
                        "trackName": result.trackName,
                        "duration": result.duration
                    }
                    for result in results
                ]
            }
            click.echo(js.dumps(output, indent=4))
        else:
            for i, result in enumerate(results, start=1):
                dur = format_duration(result.duration)
                click.secho(f"{i}) ", fg="cyan", nl=False)
                click.secho(f"{result.artistName} - {result.trackName} ", fg="green", nl=False)
                click.secho(f"({dur}) ", fg="yellow", nl=False)
                click.secho(f"[ID: {result.id}]", fg="blue")
            
    except Exception as e:
        if json:
            output = {
                "success": False,
                "error": str(e)
            }
            click.echo(js.dumps(output, indent=4))
        else:
            click.secho(f"An error occurred during search: {e}", fg="red")


@cli.command(name="transcribe", help="Transcribe a song and align its lyrics on word-level.")
@click.option("--id", "lyrics_id", type=int, help="LRCLIB ID of the song to transcribe")
@click.option("--query", help="Any query to search for the song")
@click.option("--file", required=True, type=click.Path(exists=True, dir_okay=False), help="Path to audio file")
@click.option("--output", required=True, type=click.Path(dir_okay=False, writable=True), help="Path to output file")
@click.option("--lang", default="en", help="Language for transcription (default: en)")
@click.option("--raw", is_flag=True, help="Skip alignment and just use the original timings from LRCLIB")
@click.option("--json", is_flag=True, help="Output results in JSON format")
def transcribe(lyrics_id: int, query: str, file: str, output: str, lang: str, raw: bool, json: bool):
    """Transcribe a song and align its lyrics."""
    if not lyrics_id and not query:
        if json:
            out = {
                "success": False,
                "error": "You must provide either --id or --query."
            }
            click.echo(js.dumps(out, indent=4))
        else:
            click.secho("Error: You must provide either --id or --query.", fg="red")
        return

    client = get_client()
    lyrics = None

    try:
        if query:
            click.secho(f"Searching for \"{query}\"...", fg="cyan")
            results = client.search_lyrics(q=query)
            if not results:
                click.secho("No results found for the given query.", fg="red")
                return
            lyrics = results[0]
            dur = format_duration(lyrics.duration)
            click.secho("Found: ", fg="green", nl=False)
            click.echo(f"{lyrics.artistName} - {lyrics.trackName} ({dur}) [ID: {lyrics.id}]")
        elif lyrics_id:
            lyrics = client.get_lyrics_by_id(lyrics_id)
            if not lyrics.id:
                click.secho("No lyrics found with the given ID.", fg="red")
                return

        if not lyrics:
            click.secho("Could not determine lyrics.", fg="red")
            return

        if not lyrics.syncedLyrics:
            click.secho(f"The lyrics for '{lyrics.artistName} - {lyrics.trackName}' are not synced.", fg="yellow")
            return
        click.secho(f"Importing {lyrics.artistName} - {lyrics.trackName}...", fg="cyan")

        if raw:
            result = AlignmentResult(lyrics.to_whisperx_segments())
        else:
            click.secho("Removing music from audio...", fg="cyan")
            vocals_path = remove_music(file)

            click.secho("Transcribing audio...", fg="cyan")
            result = align(lyrics, vocals_path, language_code=lang)
        
        if output.lower().endswith(".srt"):
            result.save_to_srt_file(output)
        elif output.lower().endswith(".vtt"):
            result.save_to_vtt_file(output)
        elif output.lower().endswith(".ass"):
            result.save_to_ass_file(output)
        elif output.lower().endswith(".txt"):
            result.save_to_ultrastar_file(output, artist=lyrics.artistName, title=lyrics.trackName, audio=output)
        else:
            raise Exception("Unsupported output format. Please use .srt, .vtt, .ass or .txt extension.")

        if json:
            click.echo(js.dumps({
                "success": True,
            }, indent=4))
        else:
            click.secho(f"Finished! Output saved to {output}", fg="green")

    except Exception as e:
        if json:
            out = {
                "success": False,
                "error": str(e)
            }
            click.echo(js.dumps(out, indent=4))
        else:
            click.secho(f"Failed to import/transcribe: {e}", fg="red")


def get_appdata_dir() -> Path:
    """Returns the platform-specific appdata directory for vibes."""
    home = Path.home()
    if os.name == 'nt':
        return Path(os.environ.get('APPDATA', home / 'AppData' / 'Roaming')) / 'vibes'
    elif sys.platform == 'darwin':
        return home / 'Library' / 'Application Support' / 'vibes'
    else:
        return home / '.local' / 'share' / 'vibes'

@cli.command(name="vimport")
@click.option("--youtube", required=True, help="YouTube video link")
@click.option("--lang", default="en", help="Language for transcription (default: en)")
@click.option("--raw", is_flag=True, help="Skip alignment and just use the original timings from LRCLIB")
@click.option("--json", "json_output", is_flag=True, help="Output results in JSON format")
def vimport(youtube: str, lang: str, raw: bool, json_output: bool):
    """Import a song for vibes with a single command using a youtube link."""
    client = get_client()

    try:
        if not json_output:
            click.secho(f"Extracting video information for {youtube}...", fg="cyan")
            
        import yt_dlp
        from typing import Any
        
        ydl_opts: Any = {
            'quiet': True,
            'skip_download': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube, download=False)
            video_title = info.get('title')

        if not video_title:
            raise Exception("Could not extract video title from YouTube link.")
            
        if not json_output:
            click.secho(f"Found video: {video_title}", fg="green")
            click.secho(f"Searching for \"{video_title}\"...", fg="cyan")
            
        results = client.search_lyrics(q=video_title)
        if not results:
            raise Exception("No results found for the given query.")
            
        lyrics = results[0]
        
        if not json_output:
            dur = format_duration(lyrics.duration)
            click.secho("Found: ", fg="green", nl=False)
            click.echo(f"{lyrics.artistName} - {lyrics.trackName} ({dur}) [ID: {lyrics.id}]")
            click.secho(f"Importing {lyrics.artistName} - {lyrics.trackName}...", fg="cyan")
            
        if not lyrics.syncedLyrics:
            raise Exception(f"The lyrics for '{lyrics.artistName} - {lyrics.trackName}' are not synced.")
        
        # Setup output directory
        safe_title = "".join(c for c in f"{lyrics.artistName} - {lyrics.trackName}" if c.isalnum() or c in " _-")
        output_dir = get_appdata_dir() / 'songs' / safe_title
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_txt = output_dir / "song.txt"
        
        if not json_output:
            click.secho("Downloading video from YouTube...", fg="cyan")
            click.secho("Downloading audio from YouTube...", fg="cyan")
            
        yt_result = download_youtube_video_and_audio(youtube, str(output_dir))
        audio_file = yt_result['audio']
        
        if not json_output:
            click.secho("Downloading album cover...", fg="cyan")
            
        cover_filename = download_cover(
            artist=lyrics.artistName,
            title=lyrics.trackName,
            album=lyrics.albumName,
            output_dir=str(output_dir)
        )
        
        if raw:
            result = AlignmentResult(lyrics.to_whisperx_segments())
        else:
            if not json_output:
                click.secho("Removing music from audio...", fg="cyan")
            vocals_path = remove_music(audio_file)

            if not json_output:
                click.secho("Transcribing audio...", fg="cyan")
            result = align(lyrics, vocals_path, language_code=lang)
            
        result.save_to_ultrastar_file(str(output_txt), artist=lyrics.artistName, title=lyrics.trackName, audio="audio.mp3", video="video.mp4", cover=cover_filename)
        
        if json_output:
            click.echo(js.dumps({
                "success": True,
            }, indent=4))
        else:
            click.secho(f"Finished! Output saved to {output_txt}", fg="green")

    except Exception as e:
        if json_output:
            out = {
                "success": False,
                "error": str(e)
            }
            click.echo(js.dumps(out, indent=4))
        else:
            click.secho(f"Failed to import/transcribe: {e}", fg="red")


def main():
    cli()

if __name__ == '__main__':
    main()
