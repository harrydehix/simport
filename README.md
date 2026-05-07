# AI based song import for vibes

This is a submodule of [vibes](https://github.com/harrydehix/vibes/) that is responsible for transcribing audio files based on [lrclib.net](https://lrclib.net) timings and optimizing and refining them on word level using demucs and whisperx. It is still in development.

_Features_:

- Importing a song to [vibes](https://github.com/harrydehix/vibes/) using a single youtube link (whisperx based transcription and media download through `yt-dlp` is managed for you) [[more info](#importing-a-song-for-vibes)]
- Searching for lyrics available on `lrclib.net` using various search parameters (_artist name_, _track name_, _query_): [[more info](#just-searching-for-available-lyrics)]
- Transcribing songs using an audio file and a lrclib.net ID to the desired output format (`.txt`, `.ass`, `.vtt`, `.srt`): [[more info](#transcribing-a-song-by-id)]
- Transcribing songs using an audio file and a lrclib.net search query to the desired output format (`.txt`, `.ass`, `.vtt`, `.srt`): [[more info](#transcribing-a-song-by-search-query)]

## Installation

1. Install Node.js (>=v20) from [nodejs.org](https://nodejs.org/)
2. Clone this repository
3. `cd simport && npm run install` to install the tool as cli

Try it out! `simport --help` for more information on how to use the CLI tool.

## Usage

### Just searching for available lyrics

```bash
simport search [--artist "Artist Name"] [--title "Song Title"] [--query "Optional search query"] [--json]
```

_Response_:

```
1) <Artist> - <Track Name> (<Duration>) [ID: <ID>]
2) <Artist> - <Track Name> (<Duration>) [ID: <ID>]
...
```

### Transcribing a song by ID

This will transcribe the song with the given ID and transcribe it using the provided audio file. The audio file should be in a format supported by ffmpeg (e.g., mp3, wav, etc.).

```bash
simport transcribe --id <ID> --file <Path to audio file> --output <Path to output file> [--lang <Language for transcription (default: en)>] [--raw] [--json]
```

Setting `--lang` to the original language is no guarantee for better results, but it can help in some cases.

_Response_:

```
Transcribing <Artist> - <Track Name>...
Removing music from audio...
Separated tracks will be stored in <path>...
Seperating track <path>...
Transcribing audio...
Loaded WhisperX model for language <Language> and device <Device>...
Finished! Output saved to <Path to output file>
```

### Transcribing a song by search query

This will search for songs matching the provided query and transcribe the first result. The audio file should be in a format supported by ffmpeg (e.g., mp3, wav, etc.).

```bash
simport transcribe --query "Any query" --file <Path to audio file> --output <Path to output file> [--lang <Language for transcription (default: en)>] [--raw] [--json]
```

Setting `--lang` to the original language is no guarantee for better results, but it can help in some cases.

_Response_:

```
Searching for "Any query"...
Found: <Artist> - <Track Name> (<Duration>) [ID: <ID>]
Transcribing <Artist> - <Track Name>...
Removing music from audio...
Separated tracks will be stored in <path>...
Seperating track <path>...
Transcribing audio...
Loaded WhisperX model for language <Language> and device <Device>...
Finished! Output saved to <Path to output file>
```

### Importing a song for vibes

This will extract the audio and video from the provided youtube link, search for the song on lrclib using the video title, extract the vocals using demucs, transcribe them and finally save the results to the vibes output directory. This will also automatically fetch a cover image for the song and save it to the output directory.

```bash
simport vimport --youtube <YouTube video link> [--lang <Language for transcription (default: en)>] [--raw] [--json] [--gemini-api-key <API key for Google Gemini API>]
```

_Note_: The gemini api key can also be set via GEMINI_API_KEY environment variable and is used to extract song info from YouTube title. This can be helpful if the video title does not match the song name and artist name, which can lead to better search results on lrclib.net and therefore better transcriptions.

_Response_:

```
Extracting video information for <YouTube video link>...
Found video: <Video Title>
Searching for "<Video Title>"...
Found: <Artist> - <Track Name> (<Duration>) [ID: <ID>]
Importing <Artist> - <Track Name>...
Downloading video from YouTube...
Downloading audio from YouTube...
...
Removing music from audio...
Separated tracks will be stored in <path>...
Seperating track <path>...
Transcribing audio...
Loaded WhisperX model for language <Language> and device <Device>...
Finished! Output saved to <Path to output file>
```
