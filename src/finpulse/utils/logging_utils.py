"""Logging utilities and Tee class."""

import io
import logging
from datetime import datetime, timezone



class Tee(io.TextIOBase):
    """Write to multiple streams simultaneously."""
    
    def __init__(self, *streams):
        self.streams = list(streams)
        self._closed = set()
        self._is_closed = False
    
    def write(self, s):
        if self._is_closed:
            return len(s)
        
        for st in list(self.streams):
            try:
                if hasattr(st, 'closed') and st.closed:
                    self._closed.add(st)
                    continue
                st.write(s)
                st.flush()
            except (OSError, IOError, ValueError) as e:
                # Silently remove failed streams to prevent spam
                self._closed.add(st)
        
        if self._closed:
            self.streams = [st for st in self.streams if st not in self._closed]
            self._closed.clear()
        return len(s)
    
    def flush(self):
        if self._is_closed:
            return
            
        for st in list(self.streams):
            try:
                if hasattr(st, 'closed') and st.closed:
                    self._closed.add(st)
                    continue
                st.flush()
            except (OSError, IOError, ValueError) as e:
                # Silently remove failed streams
                self._closed.add(st)
        
        if self._closed:
            self.streams = [st for st in self.streams if st not in self._closed]
            self._closed.clear()
    
    def close(self):
        """Close the Tee and mark it as closed."""
        self._is_closed = True
        self.streams.clear()
    
    @property
    def closed(self):
        """Return True if the Tee is closed."""
        return self._is_closed


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