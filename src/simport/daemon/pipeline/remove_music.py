import os
import logging
import contextlib
from demucs.separate import main as demucs_main
from simport.logger import LoggerWriter

logger = logging.getLogger(__name__)

def remove_music(audio_file: str, output_dir: str = "separated") -> str:
    """
    Uses Demucs to separate the vocals from the music in the given audio file.
    Returns the path to the isolated vocals file.
    """
    logger.info(f"Starting music removal (Demucs) for {audio_file}")
    
    args = [
        "--two-stems", "vocals",
        "-o", output_dir,
        audio_file
    ]
    
    try:
        with contextlib.redirect_stdout(LoggerWriter(logger, logging.INFO)), \
             contextlib.redirect_stderr(LoggerWriter(logger, logging.ERROR)):
            demucs_main(args)
    except Exception as e:
        logger.error(f"Demucs processing failed: {e}", exc_info=True)
        raise
    
    base_name = os.path.splitext(os.path.basename(audio_file))[0]
    vocals_path = os.path.join(output_dir, "htdemucs", base_name, "vocals.wav")
    
    if not os.path.exists(vocals_path):
        logger.error(f"Vocals file not found at expected location: {vocals_path}")
        raise FileNotFoundError(f"Vocals file not found at expected location: {vocals_path}")
    
    logger.info(f"Music removal successful. Vocals saved to: {vocals_path}")
    return vocals_path