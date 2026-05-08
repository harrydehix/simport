# Daemon API specification

This document describes the API of a daemon, that provides access to lrclib.net song search and ai based transcription. It also supports commands to import songs directly into an ultrastar song folder. It uses socket.io for communication, and is designed to be used by a client application, such as a web app or a mobile app.

## Connection

- **Protocol**: WebSockets (Socket.IO)
- **Namespace**: `/` (default)
- **Port**: Dynamically assigned or configured via Env-Var (z.B. `8000`)

---

## 1. Search API

Searches for available lyrics on lrclib.net.

### Client emits: `search`

**Payload:**

```json
{
    "artist": "string (optional)",
    "title": "string (optional)",
    "query": "string (optional)"
}
```

_(Note: At least one parameter must be provided)_

### Server emits: `search:result`

**Payload:**

```json
{
    "success": true,
    "results": [
        {
            "id": 123456,
            "artistName": "Bad Bunny",
            "trackName": "Tití Me Preguntó",
            "duration": 243
        }
    ]
}
```

### Server emits: `search:error`

**Payload:**

```json
{
    "success": false,
    "error": "Error message details"
}
```

---

## 2. Transcribe API

Transcribes a song and aligns its lyrics on word-level using a local audio file.

### Client emits: `transcribe`

**Payload:**

```json
{
    "id": "number (optional, lrclib.net ID)",
    "query": "string (optional, search query if ID is not known)",
    "file": "string (required, absolute path to local audio file)",
    "output": "string (required, absolute path to destination .txt, .srt, .ass, or .vtt)",
    "lang": "string (optional, default: 'en')",
    "raw": "boolean (optional, skip AI alignment)",
    "offset_fix": "boolean (optional, default: true)"
}
```

### Server emits: `transcribe:progress`

Used to display current status in the UI.
**Payload:**

```json
{
    "step": "string (e.g., 'searching', 'separating_audio', 'transcribing')",
    "message": "string (e.g., 'Removing music from audio...')",
    "percent": "number (optional, 0-100)"
}
```

### Server emits: `transcribe:result`

**Payload:**

```json
{
    "success": true,
    "output": "path/to/output/file.txt"
}
```

### Server emits: `transcribe:error`

**Payload:**

```json
{
    "success": false,
    "error": "Error message details"
}
```

---

## 3. VImport API (YouTube / Video Import)

Imports a song from a YouTube link directly into a specified output folder. Includes downloading, separating audio, and transcribing.

### Client emits: `vimport`

**Payload:**

```json
{
    "youtube": "string (required, YouTube URL)",
    "output": "string (required, absolute path to destination folder)",
    "lang": "string (optional)",
    "infer_lang": "boolean (optional, default false)",
    "offset_fix": "boolean (optional, default: true)",
    "gemini_api_key": "string (optional)",
    "raw": "boolean (optional, skip AI alignment)"
}
```

### Server emits: `vimport:progress`

Used to display current status in the UI.
**Payload:**

```json
{
    "step": "string (e.g., 'downloading_video', 'downloading_cover', 'separating_audio', 'transcribing')",
    "message": "string (e.g., 'Downloading video from YouTube...')",
    "percent": "number (optional, 0-100)"
}
```

### Server emits: `vimport:result`

**Payload:**

```json
{
    "success": true,
    "output": "path/to/output_dir/song.txt"
}
```

### Server emits: `vimport:error`

**Payload:**

```json
{
    "success": false,
    "error": "Error message details"
}
```
