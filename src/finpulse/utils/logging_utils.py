"""Logging utilities and Tee class."""

import io
import logging
from datetime import datetime, timezone
from typing import Any


class Tee(io.TextIOBase):
    """Write to multiple streams simultaneously."""
    
    def __init__(self, *streams):
        self.streams = list(streams)
        self._closed = set()
    
    def write(self, s):
        for st in list(self.streams):
            try:
                st.write(s)
                st.flush()
            except (OSError, IOError, ValueError) as e:
                logging.warning(f"Failed to write to stream: {e}")
                self._closed.add(st)
        if self._closed:
            self.streams = [st for st in self.streams if st not in self._closed]
            self._closed.clear()
        return len(s)
    
    def flush(self):
        for st in list(self.streams):
            try:
                st.flush()
            except (OSError, IOError) as e:
                logging.warning(f"Failed to flush stream: {e}")
                self._closed.add(st)
        if self._closed:
            self.streams = [st for st in self.streams if st not in self._closed]
            self._closed.clear()


def utc_log_name(is_dry: bool) -> str:
    """Generate UTC timestamp-based log filename."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    return f"Log {ts}{' dry-run' if is_dry else ''}.txt"


def setup_logging() -> None:
    """Configure basic logging."""
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(message)s'
    )