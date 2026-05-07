from vibes_song_importer.lrclib.api import Lyrics
import whisperx
import torch
import re
import math

def clean_lyrics_text(text: str) -> str:
    """Entfernt Metadaten wie [Chorus] oder (x2), die WhisperX verwirren könnten."""
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    return text.strip()

# please document the dictionary fully!!! (typesafe)
class AlignmentResult:
    """Represents the result of the alignment process."""
    def __init__(self, segments: list[dict]):
        self.segments = segments

    def _format_time(self, seconds: float, separator: str = ",") -> str:
        """Formats seconds into SRT time format (HH:MM:SS,ms)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds - int(seconds)) * 1000)
        return f"{hours:02}:{minutes:02}:{secs:02}{separator}{milliseconds:03}"

    def save_to_srt_file(self, file_path: str):
        """Saves the aligned segments to an SRT file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            for i, seg in enumerate(self.segments, start=1):
                start_time = self._format_time(seg['start'])
                end_time = self._format_time(seg['end'])
                f.write(f"{i}\n{start_time} --> {end_time}\n{seg['text']}\n\n")
    
    def save_to_vtt_file(self, file_path: str):
        """Saves the aligned segments to a WebVTT file with inline word timestamps."""
        with open(file_path, 'w', encoding='utf-8') as f:
            # VTT Dateien müssen zwingend mit diesem Header beginnen
            f.write("WEBVTT\n\n")
            
            for i, seg in enumerate(self.segments, start=1):
                start_time = self._format_time(seg.get('start', 0.0), separator=".")
                end_time = self._format_time(seg.get('end', 0.0), separator=".")
                
                # Der Index (i) ist bei VTT optional, schadet aber nicht für die Struktur
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                
                # Prüfen, ob wir detaillierte Wort-Informationen von WhisperX haben
                if "words" in seg:
                    line_parts = []
                    for word_obj in seg["words"]:
                        word_text = word_obj.get("word", "").strip()
                        if not word_text:
                            continue
                        
                        if "start" in word_obj:
                            word_time = self._format_time(word_obj["start"], separator=".")
                            line_parts.append(f"{word_text}<{word_time}>")
                        else:
                            # Fallback: Wort konnte nicht gematcht werden
                            line_parts.append(word_text)
                    
                    formatted_line = " ".join(line_parts)
                    f.write(f"{formatted_line}\n\n")
                else:
                    # Fallback auf reinen Zeilentext, falls keine Wörter erkannt wurden
                    text = seg.get('text', '').strip()
                    f.write(f"{text}\n\n")
    
    def _format_ass_time(self, seconds: float) -> str:
        """ASS Format verlangt H:MM:SS.cs (Hundertstelsekunden)"""
        if math.isnan(seconds):
            return "0:00:00.00"
        
        # Sichere Rundung, um Rollover-Bugs (z.B. 59.999s) zu vermeiden
        total_cs = int(round(seconds * 100))
        hours = total_cs // 360000
        total_cs %= 360000
        minutes = total_cs // 6000
        total_cs %= 6000
        secs = total_cs // 100
        cs = total_cs % 100
        
        return f"{hours}:{minutes:02d}:{secs:02d}.{cs:02d}"

    def save_to_ass_file(self, file_path: str):
        """Speichert die Lyrics als echtes animiertes Karaoke für den VLC Player & Videoschnitt."""
        
        # Das ist das "Stylesheet" der Untertitel.
        # Hier ist voreingestellt: Weißer Text, der sich beim Singen Gelb füllt, mit schwarzem Rand.
        ass_header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Karaoke,Arial,80,&H0000FFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,10,10,50,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(ass_header)
            
            for seg in self.segments:
                start_time = seg.get('start', 0.0)
                end_time = seg.get('end', 0.0)
                
                ass_start = self._format_ass_time(start_time)
                ass_end = self._format_ass_time(end_time)
                
                # Falls keine Wörter erkannt wurden, normale Zeile ausgeben
                if "words" not in seg or not seg["words"]:
                    text = seg.get('text', '').strip()
                    f.write(f"Dialogue: 0,{ass_start},{ass_end},Karaoke,,0000,0000,0000,,{text}\n")
                    continue
                
                line_text = ""
                current_time = start_time
                
                for word_obj in seg["words"]:
                    if "start" not in word_obj or "end" not in word_obj:
                        line_text += f"{word_obj.get('word', '')} "
                        continue
                        
                    w_start = word_obj["start"]
                    w_end = word_obj["end"]
                    word = word_obj["word"].strip()
                    
                    # 1. Pause VOR dem Wort berechnen (in Hundertstelsekunden)
                    # (Damit die Farbe nicht sofort weiterspringt, wenn der Sänger kurz atmet)
                    gap = w_start - current_time
                    if gap > 0.01:
                        gap_cs = int(round(gap * 100))
                        line_text += f"{{\\k{gap_cs}}}"
                        
                    # 2. Dauer des Wortes berechnen
                    dur_cs = int(round((w_end - w_start) * 100))
                    
                    # \kf sorgt für den weichen, flüssigen Farbeffekt (wie bei echter Karaoke)
                    line_text += f"{{\\kf{dur_cs}}}{word} "
                    
                    current_time = w_end
                    
                final_line = line_text.strip()
                f.write(f"Dialogue: 0,{ass_start},{ass_end},Karaoke,,0000,0000,0000,,{final_line}\n")

    def save_to_ultrastar_file(self, file_path: str, artist: str = "Unknown", title: str = "Unknown", audio: str = "audio.mp3"):
        """Saves the lyrics in the UltraStar TXT format."""
        bpm = 1500
        ms_per_beat = 10

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"#TITLE:{title}\n")
            f.write(f"#ARTIST:{artist}\n")
            f.write(f"#AUDIO:{audio}\n")
            f.write(f"#BPM:{bpm}\n")
            f.write(f"#GAP:0\n")
            
            for seg in self.segments:
                start_time = seg.get('start', 0.0)
                
                # Zuerst prüfen ob wir Wort-Timings haben
                if "words" not in seg or not seg["words"]:
                    start_ms = int(seg.get('start', 0.0) * 1000)
                    end_ms = int(seg.get('end', 0.0) * 1000)
                    start_beat = start_ms // ms_per_beat
                    dur_beat = max(1, (end_ms - start_ms) // ms_per_beat)
                    text = seg.get('text', '').strip()
                    
                    # ":" steht für normale Noten, gefolgt von StartBeat, Länge, Tonhöhe(0), und Text
                    f.write(f": {start_beat} {dur_beat} 0 {text}\n")
                    f.write(f"- {start_beat + dur_beat}\n")
                    continue
                
                for word_obj in seg["words"]:
                    if "start" not in word_obj or "end" not in word_obj:
                        continue
                        
                    w_start_ms = int(word_obj["start"] * 1000)
                    w_end_ms = int(word_obj["end"] * 1000)
                    
                    start_beat = w_start_ms // ms_per_beat
                    dur_beat = max(1, (w_end_ms - w_start_ms) // ms_per_beat)
                    word = word_obj["word"].strip()
                    
                    f.write(f": {start_beat} {dur_beat} 0 {word} \n")
                
                # End of segment is marked by a "-"
                end_ms = int(seg.get('end', 0.0) * 1000)
                break_beat = end_ms // ms_per_beat
                f.write(f"- {break_beat}\n")
                
            f.write("E\n")


def align(lyrics: Lyrics, audio_file: str, language_code: str = "en") -> AlignmentResult:
    """Aligns the lyrics with the audio file word by word."""
    if not lyrics.syncedLyrics or not lyrics.plainLyrics:
        raise ValueError("No alignment possible: missing synced lyrics")
    
    whisperx_segments = lyrics.to_whisperx_segments()
    
    for seg in whisperx_segments:
        seg["text"] = clean_lyrics_text(seg["text"])

    audio = whisperx.load_audio(audio_file)

    device = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"Loading WhisperX model for language '{language_code}' on device '{device}'...")

    model_a, metadata = whisperx.load_align_model(language_code=language_code, device=device)

    result = whisperx.align(
        whisperx_segments, 
        model_a, 
        metadata, 
        audio, 
        device, 
        return_char_alignments=False
    )

    return AlignmentResult(segments=result["segments"])