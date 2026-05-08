
from typing import TypedDict, List, Optional

class WordData(TypedDict, total=False):
    """Represents a single aligned word."""
    word: str
    start: float
    end: float
    score: float

class SegmentData(TypedDict, total=False):
    """Represents a synchronized text segment from WhisperX."""
    text: str
    start: float
    end: float
    words: List[WordData]