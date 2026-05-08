# AI based song import for vibes / ultrastar

This is a submodule of [vibes](https://github.com/harrydehix/vibes/) that is responsible for transcribing songs based on [lrclib.net](https://lrclib.net) timings and refining them on word level using AI (demucs and whisperx). It also supports automatically fetching media using `yt-dlp` and extracting song info from YouTube video titles using the Google Gemini API.

It can be used as a standalone application that runs as a daemon and exposes a [socket.io API](./api.md) for client applications to interact with. There is also a CLI tool that can be used to interact with the daemon directly from the command line.

_Features_:

- Importing a song to UltraStar applications using a single youtube link (WhisperX based transcription and media download through `yt-dlp` is managed for you): [[more info](#importing-a-song-from-youtube)]
- Searching for lyrics available on `lrclib.net` using various search parameters (_artist name_, _track name_, _query_): [[more info](#just-searching-for-available-lyrics)]
- Transcribing songs using an audio file and a lrclib.net ID with the desired output format (`.txt` UltraStar, `.ass`, `.vtt`, `.srt`): [[more info](#transcribing-a-song-by-id)]
- Transcribing songs using an audio file and a lrclib.net search query with the desired output format (`.txt` UltraStar, `.ass`, `.vtt`, `.srt`): [[more info](#transcribing-a-song-by-search-query)]

## Installation

Just run `python ./install.py` to install the tool as cli. Windows support is tested, other platforms should work but are not tested yet. Report any issues you encounter.

Try it out! `simport --help` for more information on how to use the CLI tool.

## Usage

Before running any CLI commands, start the daemon (in a background terminal):

```bash
simport daemon [--port 8000] [--host 127.0.0.1]
```

_(By default, the CLI looks for the daemon at `http://127.0.0.1:8000`. You can override this using the `SIMPORT_DAEMON_URL` environment variable)._

For client application developers (e.g. Electron/Vue), you can connect directly to this Socket.IO server. See [api.md](./api.md) for the detailed WebSocket API specification.

### Just searching for available lyrics

This will search for available lyrics on lrclib.net using the provided search parameters. At least one parameter must be provided.

```bash
simport search [--artist "Artist Name"] [--title "Song Title"] [--query "Optional search query"]
```

_Example_:

```sh
$ simport search --query "Calvin Harris"
```

```
1) Primal Scream - Uptown (Calvin Harris Remix) (3.0:57.0) [ID: 129364]
2) Calvin Harris - Acceptable in the 80s (5.0:35.0) [ID: 139431]
3) Calvin Harris - Awooga (3.0:51.0) [ID: 139527]
4) Calvin Harris - Blue (3.0:40.0) [ID: 139680]
...
```

### Transcribing a song by ID

This will transcribe a song using the base timings available on lrclib.net for the specified song. The audio file should be in a format supported by ffmpeg (e.g., mp3, wav, etc.).

The ID will be used to fetch the presynced song lyrics from lrclib.net.

```bash
simport transcribe --id <ID> --file <Path to audio file> --output <Path to output file> [--lang <Language for transcription (default: en)>] [--raw] [--offset-fix/--no-offset-fix]
```

Setting `--lang` to the original language is no guarantee for better results, but it can help in some cases.

_Example_:

```sh
$ simport transcribe --id 141250 --file "./data/limits.mp3" --output "test.txt"
```

```sh
[searching] Fetching lyrics for ID 141250...
[transcribing_init] Transcribing Calvin Harris - Limits...
[separating_audio] Removing music from audio...
[transcribing] Transcribing audio (alignment)...
[saving] Saving output file...
Finished! Output saved to D:\Code\vibes-ai-based-import\test.txt
```

### Transcribing a song by search query

This will transcribe a song using the base timings available on lrclib.net for the specified song. The audio file should be in a format supported by ffmpeg (e.g., mp3, wav, etc.).

The query will be used to search for the presynced song lyrics on lrclib.net.

```bash
simport transcribe --query "Any query" --file <Path to audio file> --output <Path to output file> [--lang <Language for transcription (default: en)>] [--raw] [--offset-fix/--no-offset-fix]
```

Setting `--lang` to the original language is no guarantee for better results, but it can help in some cases.

_Example_:

```sh
$ simport transcribe --query "Promises - Calvin Harris" --file "./data/promises.mp3" --output "test.txt"
```

```sh
[searching] Searching for "Promises - Calvin Harris"...
[transcribing_init] Transcribing Calvin Harris feat. Sam Smith - Promises (Mixed)...
[separating_audio] Removing music from audio...
[transcribing] Transcribing audio (alignment)...
[saving] Saving output file...
Finished! Output saved to D:\Code\vibes-ai-based-import\test.txt
```

### Importing a song from YouTube

This will extract the audio and video from the provided youtube link, search for the song on lrclib.net using the video title, refine the line timings on word level using demucs and whisperx and finally save the results to the given output directory. This will also automatically fetch a cover image for the song and save it to the output directory.

```bash
simport vimport --youtube <YouTube video link> [--output <Path to output directory>] [--lang <Language for transcription (default: en)>] [--raw] [--gemini-api-key <API key for Google Gemini API>] [--offset-fix/--no-offset-fix]
```

_Note_: The optional gemini api key can also be set via GEMINI_API_KEY environment variable and is used to extract song info from YouTube title. This can be helpful if the video title does not match the song name and artist name, which can lead to better search results on lrclib.net and therefore better transcriptions. Create an api key [here](https://ai.google.dev/gemini-api/docs/api-key).

_Example_:

```sh
$ simport vimport --youtube https://youtu.be/2Oty9ENyZUc?si=D5j6gzwikxIQgTWs --gemini-api-key <key> --output C:\Users\<user>\AppData\Roaming\vibes\songs
```

```sh
[extracting_info] Extracting video information for https://youtu.be/2Oty9ENyZUc?si=D5j6gzwikxIQgTWs...
[analyzing_title] Extracting song info from video title using Gemini API...
[searching] Searching for "Paula Hartmann - Veuve"...
[downloading_video] Downloading video and audio from YouTube...
[downloading_cover] Downloading album cover...
[separating_audio] Removing music from audio...
[transcribing] Transcribing audio (alignment)...
[saving] Saving output file...
Finished! Output saved to C:\Users\<user>\AppData\Roaming\vibes\songs\Paula Hartmann - Veuve\song.txt
```

The structure of the output directory will be as follows:

```sh
output_directory/
└── Artist - Title/
    ├── song.txt    # ultrastar file format
    ├── cover.jpg   # only if a cover image was found
    ├── audio.mp3   # audio extracted from the YouTube video
    └── video.mp4   # video extracted from the YouTube video
```
