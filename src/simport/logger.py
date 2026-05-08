import logging
import sys

class LoggerWriter:
    """Redirects write streams (stdout/stderr) to a logger."""
    def __init__(self, logger_obj, level):
        self.logger = logger_obj
        self.level = level

    def write(self, message: str) -> int:
        msg = message.strip()
        # Progress bars and empty messages can spam the logs, we ignore empty lines
        if msg:
            self.logger.log(self.level, msg)
        return len(message)

    def flush(self):
        pass

class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[90m',       # Grey
        'INFO': '\033[36m',        # Cyan
        'WARNING': '\033[33m',     # Yellow
        'ERROR': '\033[31m',       # Red
        'CRITICAL': '\033[1;31m',  # Bold Red
    }
    RESET = '\033[0m'

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        fmt = f"{color}%(asctime)s | %(levelname)-8s | %(name)s | %(message)s{self.RESET}"
        formatter = logging.Formatter(fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)

def setup_logger():
    """
    Set up a colored logging format for the entire application.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColoredFormatter())
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove existing handlers to prevent duplicates (e.g., from basicConfig)
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
        
    root_logger.addHandler(handler)

    # Disable overly verbose loggers from dependencies
    logging.getLogger('engineio').setLevel(logging.WARNING)
    logging.getLogger('socketio').setLevel(logging.WARNING)
    
    return root_logger
