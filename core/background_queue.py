# core/background_queue.py
"""
Background worker queue for async transcription and TTS.
Prevents main thread blocking during heavy operations.
"""

import os
import queue
import threading
import time
import traceback
from pathlib import Path
from datetime import datetime

# Debug logging
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
DEBUG_LOG = LOG_DIR / "last_session_debug.log"
IMPROVEMENTS_LOG = LOG_DIR / "improvements.log"


def log_debug(message: str):
    """Log debug message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    line = f"[{timestamp}] {message}\n"
    try:
        with open(DEBUG_LOG, "a", encoding="utf-8") as f:
            f.write(line)
    except:
        pass


def log_improvement(message: str):
    """Log to improvements log."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}\n"
    try:
        with open(IMPROVEMENTS_LOG, "a", encoding="utf-8") as f:
            f.write(line)
    except:
        pass


class BackgroundWorker:
    """Thread-safe background worker for heavy operations."""
    
    def __init__(self, name: str = "worker"):
        self.name = name
        self._queue = queue.Queue()
        self._running = False
        self._thread = None
        self._error_callback = None
        
    def start(self):
        """Start the worker thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name=f"bg_{self.name}")
        self._thread.start()
        log_debug(f"BackgroundWorker '{self.name}' started")
        
    def stop(self):
        """Stop the worker thread."""
        self._running = False
        self._queue.put(None)  # Poison pill
        if self._thread:
            self._thread.join(timeout=2.0)
        log_debug(f"BackgroundWorker '{self.name}' stopped")
        
    def submit(self, func, *args, callback=None, error_callback=None, **kwargs):
        """Submit a task to the worker queue."""
        task = {
            'func': func,
            'args': args,
            'kwargs': kwargs,
            'callback': callback,
            'error_callback': error_callback or self._error_callback,
            'submit_time': time.time()
        }
        self._queue.put(task)
        log_debug(f"Task submitted to '{self.name}': {func.__name__ if hasattr(func, '__name__') else 'lambda'}")
        
    def set_error_callback(self, callback):
        """Set global error callback."""
        self._error_callback = callback
        
    def _run(self):
        """Worker thread main loop."""
        while self._running:
            try:
                task = self._queue.get(timeout=0.5)
                if task is None:
                    break
                    
                func = task['func']
                args = task['args']
                kwargs = task['kwargs']
                callback = task['callback']
                error_callback = task['error_callback']
                submit_time = task['submit_time']
                
                start_time = time.time()
                queue_time = start_time - submit_time
                log_debug(f"Task starting (queued {queue_time:.2f}s): {func.__name__ if hasattr(func, '__name__') else 'task'}")
                
                try:
                    result = func(*args, **kwargs)
                    elapsed = time.time() - start_time
                    log_debug(f"Task completed in {elapsed:.2f}s")
                    
                    if callback:
                        try:
                            callback(result)
                        except Exception as e:
                            log_debug(f"Callback error: {e}")
                            
                except Exception as e:
                    elapsed = time.time() - start_time
                    error_msg = f"Task failed after {elapsed:.2f}s: {e}"
                    log_debug(error_msg)
                    log_debug(traceback.format_exc())
                    
                    if error_callback:
                        try:
                            error_callback(e, str(e))
                        except:
                            pass
                            
            except queue.Empty:
                continue
            except Exception as e:
                log_debug(f"Worker loop error: {e}")


# Global workers
_transcription_worker = None
_tts_worker = None


def get_transcription_worker() -> BackgroundWorker:
    """Get or create transcription worker."""
    global _transcription_worker
    if _transcription_worker is None:
        _transcription_worker = BackgroundWorker("transcription")
        _transcription_worker.start()
    return _transcription_worker


def get_tts_worker() -> BackgroundWorker:
    """Get or create TTS worker."""
    global _tts_worker
    if _tts_worker is None:
        _tts_worker = BackgroundWorker("tts")
        _tts_worker.start()
    return _tts_worker


def shutdown_workers():
    """Shutdown all workers."""
    global _transcription_worker, _tts_worker
    if _transcription_worker:
        _transcription_worker.stop()
        _transcription_worker = None
    if _tts_worker:
        _tts_worker.stop()
        _tts_worker = None
