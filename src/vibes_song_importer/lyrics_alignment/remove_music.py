import os
from demucs.separate import main as demucs_main

def remove_music(audio_file: str, output_dir: str = "separated") -> str:
    """
    Uses Demucs to separate the vocals from the music in the given audio file.
    Returns the path to the isolated vocals file.
    """
    
    args = [
        "--two-stems", "vocals",
        "-o", output_dir,
        audio_file
    ]
    
    demucs_main(args)
    
    base_name = os.path.splitext(os.path.basename(audio_file))[0]
    vocals_path = os.path.join(output_dir, "htdemucs", base_name, "vocals.wav")
    
    if not os.path.exists(vocals_path):
        raise FileNotFoundError(f"Vocals file not found at expected location: {vocals_path}")
        
    return vocals_path