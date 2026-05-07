# AI based song import for vibes

This is a submodule of [vibes](https://github.com/harrydehix/vibes/) that is responsible for transcribing audio files based on [lrclib.net](https://lrclib.net) timings and optimizing and refining them on word level using demucs and whisperx. It is still in development.

_Features_:

- Transcribe audio files available on _lrclib_ on word level
- Output formats: `.ass`, `.vtt`, `.srt`
- `--json` output for machine readability and further processing

## Prerequisites

- Pytorch (`https://pytorch.org/get-started/locally/`) - use a CUDA installation for optimized performance
- ffmpeg (`https://ffmpeg.org/download.html`) - shared, full build in path (v7.0)
- Python 3.12
- [uv](https://docs.astral.sh/uv/) installed and `uv sync` executed

## CLI Usage

Execute `./install.bat` to install the CLI tool `simport` After that, you can use the following commands:

### Just searching for available lyrics (lrclib)

```bash
simport search [--artist "Artist Name"] [--title "Song Title"] [--query "Optional search query"] [--json]
```

_Response_:

```
1) <Artist> - <Track Name> (<Duration>) [ID: <ID>]
2) <Artist> - <Track Name> (<Duration>) [ID: <ID>]
...
```

### Importing a song by ID (lrclib + whisperx)

This will import the song with the given ID and transcribe it using the provided audio file. The audio file should be in a format supported by ffmpeg (e.g., mp3, wav, etc.).

```bash
simport import --id <ID> --file <Path to audio file> --output <Path to output file> [--lang <Language for transcription (default: en)>] [--raw] [--json]
```

Setting `--lang` to the original language is no guarantee for better results, but it can help in some cases.

_Response_:

```
Importing <Artist> - <Track Name>...
Removing music from audio...
Separated tracks will be stored in <path>...
Seperating track <path>...
Transcribing audio...
Loaded WhisperX model for language <Language> and device <Device>...
Finished! Output saved to <Path to output file>
```

### Importing a song by search query (lrclib + whisperx)

This will search for songs matching the provided query and import the first result. The audio file should be in a format supported by ffmpeg (e.g., mp3, wav, etc.).

```bash
simport import --query "Any query" --file <Path to audio file> --output <Path to output file> [--lang <Language for transcription (default: en)>] [--raw] [--json]
```

Setting `--lang` to the original language is no guarantee for better results, but it can help in some cases.

_Response_:

```
Searching for "Any query"...
Found: <Artist> - <Track Name> (<Duration>) [ID: <ID>]
Importing <Artist> - <Track Name>...
Removing music from audio...
Separated tracks will be stored in <path>...
Seperating track <path>...
Transcribing audio...
Loaded WhisperX model for language <Language> and device <Device>...
Finished! Output saved to <Path to output file>
```
