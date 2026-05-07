import click
from vibes_song_importer.lrclib.api import LRCLibClient
from vibes_song_importer.lyrics_alignment.alignment import align
from vibes_song_importer.lyrics_alignment.remove_music import remove_music

def get_client() -> LRCLibClient:
    return LRCLibClient(
        app_name="vibes-ai-based-import",
        version="1.0.0",
        url="https://github.com/vibe-ai-importer/dummy"
    )

def format_duration(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    return f"{m:02}:{s:02}"


@click.group()
def cli():
    """AI based song import for vibes."""
    pass


@cli.command(name="search")
@click.option("--artist", help="Artist Name")
@click.option("--title", help="Song Title")
@click.option("--query", help="Optional search query")
def search(artist: str, title: str, query: str):
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
            click.secho("No results found.", fg="yellow")
            return
        

        for i, result in enumerate(results, start=1):
            dur = format_duration(result.duration)
            click.secho(f"{i}) ", fg="cyan", nl=False)
            click.secho(f"{result.artistName} - {result.trackName} ", fg="green", nl=False)
            click.secho(f"({dur}) ", fg="yellow", nl=False)
            click.secho(f"[ID: {result.id}]", fg="blue")
            
    except Exception as e:
        click.secho(f"An error occurred during search: {e}", fg="red")


@cli.command(name="import")
@click.option("--id", "lyrics_id", type=int, help="Import the song by ID")
@click.option("--query", help="Any query to search for the song")
@click.option("--file", required=True, type=click.Path(exists=True, dir_okay=False), help="Path to audio file")
@click.option("--output", required=True, type=click.Path(dir_okay=False, writable=True), help="Path to output file")
@click.option("--lang", default="en", help="Language for transcription (default: en)")
def import_song(lyrics_id: int, query: str, file: str, output: str, lang: str):
    """Import a song and transcribe/align its lyrics."""
    if not lyrics_id and not query:
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
        else:
            click.secho("Unsupported output format. Please use .srt, .vtt or .ass extension.", fg="red")
            return

        click.secho(f"Finished! Output saved to {output}", fg="green")

    except Exception as e:
        click.secho(f"Failed to import/transcribe: {e}", fg="red")


def main():
    cli()

if __name__ == '__main__':
    main()
