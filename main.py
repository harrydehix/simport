from vibes_song_importer.lrclib import LRCLibClient, Lyrics, CryptoChallenge, LRCLibError

# ==========================================
# Example usage
# ==========================================
if __name__ == "__main__":
    # Instantiate client (Please adapt the names to your project)
    client = LRCLibClient(
        app_name="MyPythonScript", 
        version="0.1.0", 
        url="https://github.com/yourname/yourproject"
    )

    print("--- Search for 'I Want to Live' by Borislav Slavov ---")
    try:
        result = client.get_lyrics(
            track_name="I Want to Live",
            artist_name="Borislav Slavov",
            album_name="Baldur's Gate 3 (Original Game Soundtrack)",
            duration=233
        )
        print(f"Found: {result.trackName} (ID: {result.id})")
        print("First lines (Plain):")
        print((result.plainLyrics or "")[:100] + "...\n")
        print("First lines (Synced):")
        for time, line in (result.syncedLyrics or [])[:5]: # Show only the first 5 lines
            print(f"[{time:.2f}s] {line}")
    except LRCLibError as e:
        print(f"Error or not found: {e}\n")

    print("--- General search (Portal Still Alive) ---")
    search_results = client.search_lyrics(q="still alive portal")
    for res in search_results[:3]: # Show only the first 3
        print(f"- {res.trackName} by {res.artistName} (ID: {res.id})")