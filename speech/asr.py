# E:\ai_desktop_assistant\speech\asr.py
"""
Advanced Automatic Speech Recognition with:
- CUDA detection cached at startup (no repeated DLL errors)
- Automatic model downgrade for CPU (large-v2 -> small for speed)
- Background transcription support
- Hold-to-record and Toggle PTT modes
- Max recording duration (300s default)
- WebRTC VAD for voice activity detection
- noisereduce for noise suppression
- Confidence tracking and logging
"""

import os
import sys
import queue
import threading
import tempfile
import time
import json
import logging
from pathlib import Path
import numpy as np
from datetime import datetime

# Audio libraries
try:
    import sounddevice as sd
    import soundfile as sf
    AUDIO_AVAILABLE = True
except ImportError:
    sd = None
    sf = None
    AUDIO_AVAILABLE = False

# Noise reduction
try:
    import noisereduce as nr
    NR_AVAILABLE = True
except ImportError:
    nr = None
    NR_AVAILABLE = False

# Voice Activity Detection
try:
    import webrtcvad
    VAD_AVAILABLE = True
except ImportError:
    webrtcvad = None
    VAD_AVAILABLE = False

# faster-whisper
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WhisperModel = None
    WHISPER_AVAILABLE = False

# Configuration from environment
DEVICE = os.getenv("DEVICE", "cuda")
STT_MODEL = os.getenv("STT_MODEL", "large-v2")
STT_MODEL_CPU = os.getenv("STT_MODEL_CPU", "small")  # Faster model for CPU
PTT_MODE = os.getenv("PTT_MODE", "toggle")
PTT_MAX_SECONDS = int(os.getenv("PTT_MAX_SECONDS", "300"))
CONFIDENCE_THRESHOLD = float(os.getenv("TRANSCRIBE_CONFIDENCE_THRESHOLD", "0.45"))

SAMPLE_RATE = 16000
CHANNELS = 1
BLOCKSIZE = 1600  # 100ms at 16kHz

# Logging setup
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

stt_log_path = LOG_DIR / "stt_transcripts.log"
debug_log_path = LOG_DIR / "last_session_debug.log"
improvements_log_path = LOG_DIR / "improvements.log"

logging.basicConfig(level=logging.INFO)
stt_logger = logging.getLogger("stt")
stt_handler = logging.FileHandler(stt_log_path)
stt_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
stt_logger.addHandler(stt_handler)

def log_debug(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    try:
        with open(debug_log_path, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] [ASR] {msg}\n")
    except:
        pass

def log_improvement(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(improvements_log_path, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
    except:
        pass

# Load mic calibration if available
MIC_CONFIG_PATH = Path(__file__).parent.parent / "config" / "mic.json"
VAD_AGGRESSIVENESS = 2

if MIC_CONFIG_PATH.exists():
    try:
        with open(MIC_CONFIG_PATH) as f:
            mic_config = json.load(f)
            VAD_AGGRESSIVENESS = mic_config.get("vad_aggressiveness", 2)
    except:
        pass


# ============== CUDA DETECTION (CACHED) ==============
_cuda_available = None

def check_cuda_available() -> bool:
    """Check CUDA availability ONCE at startup. Cache result."""
    global _cuda_available
    if _cuda_available is not None:
        return _cuda_available
    
    if DEVICE != "cuda":
        _cuda_available = False
        log_improvement("CUDA status: disabled by config (DEVICE != cuda)")
        print("[ASR] CUDA disabled by config")
        return False
    
    try:
        import ctranslate2
        cuda_count = ctranslate2.get_cuda_device_count()
        if cuda_count == 0:
            _cuda_available = False
            log_improvement("CUDA status: no CUDA devices found")
            print("[ASR] No CUDA devices found")
            return False
        
        # Try to actually load a tiny test to verify cuBLAS
        try:
            test_model = WhisperModel("tiny", device="cuda", compute_type="float16")
            del test_model
            _cuda_available = True
            log_improvement("CUDA status: available and working")
            print("[ASR] CUDA verified working")
            return True
        except Exception as e:
            if 'cublas' in str(e).lower():
                _cuda_available = False
                log_improvement(f"CUDA status: unavailable (cuBLAS missing) -> using CPU fallback")
                print(f"[ASR] CUDA unavailable (cuBLAS missing) - using CPU")
                return False
            else:
                _cuda_available = False
                log_improvement(f"CUDA status: unavailable ({e}) -> using CPU fallback")
                print(f"[ASR] CUDA check failed: {e}")
                return False
    except Exception as e:
        _cuda_available = False
        log_improvement(f"CUDA status: check failed ({e})")
        print(f"[ASR] CUDA detection error: {e}")
        return False


class ASREngine:
    """Advanced speech recognition engine with hold/toggle PTT."""

    def __init__(self, model_name: str = None, device: str = None):
        # Check CUDA once at startup
        self.cuda_available = check_cuda_available()
        
        # Choose device and model based on CUDA availability
        if self.cuda_available:
            self.device = "cuda"
            self.model_name = model_name or STT_MODEL
            self.compute_type = "float16"
        else:
            self.device = "cpu"
            # Use faster model on CPU for responsiveness
            self.model_name = model_name or STT_MODEL_CPU
            self.compute_type = "int8"
            if STT_MODEL == "large-v2":
                print(f"[ASR] CPU mode: using '{self.model_name}' instead of 'large-v2' for speed")
                log_improvement(f"Model switched: large-v2 -> {self.model_name} for CPU speed")
        
        self.model = None
        self.vad = None
        self.stream = None

        # Recording state
        self._recording = False
        self._frames = []
        self._record_start_time = None
        self._last_audio_time = None
        self._lock = threading.Lock()
        
        # Ready state for PTT reattachment
        self._ready_for_ptt = True

        # PTT mode
        self.ptt_mode = PTT_MODE
        self.max_duration = PTT_MAX_SECONDS
        self.confidence_threshold = CONFIDENCE_THRESHOLD

        # Callbacks
        self.on_recording_start = None
        self.on_recording_stop = None
        self.on_transcription_complete = None
        self.on_mic_error = None
        self.on_low_confidence = None

        # Initialize
        self._init_model()
        self._init_vad()

    def _init_model(self):
        if not WHISPER_AVAILABLE:
            print("[ASR] faster-whisper not installed!")
            return
        try:
            print(f"[ASR] Loading {self.model_name} on {self.device} ({self.compute_type})...")
            log_debug(f"Loading model: {self.model_name} on {self.device}")
            start = time.time()
            self.model = WhisperModel(self.model_name, device=self.device, compute_type=self.compute_type)
            elapsed = time.time() - start
            print(f"[ASR] Model loaded successfully ({elapsed:.1f}s)")
            log_debug(f"Model loaded in {elapsed:.1f}s")
            log_improvement(f"ASR model loaded: {self.model_name} on {self.device} in {elapsed:.1f}s")
        except Exception as e:
            print(f"[ASR] Model error: {e}")
            log_debug(f"Model load error: {e}")
            # Last resort fallback
            if self.device == "cuda":
                print("[ASR] Falling back to CPU...")
                self.device = "cpu"
                self.compute_type = "int8"
                self.model_name = STT_MODEL_CPU
                try:
                    self.model = WhisperModel(self.model_name, device="cpu", compute_type="int8")
                    print(f"[ASR] CPU fallback model loaded: {self.model_name}")
                except Exception as e2:
                    print(f"[ASR] CPU fallback failed: {e2}")

    def _init_vad(self):
        if not VAD_AVAILABLE:
            print("[ASR] webrtcvad not installed, VAD disabled")
            return
        try:
            self.vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)
            print(f"[ASR] VAD initialized (level={VAD_AGGRESSIVENESS})")
        except Exception as e:
            print(f"[ASR] VAD error: {e}")

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback for audio stream - captures frames while recording."""
        if self._recording:
            self._frames.append(indata.copy())
            self._last_audio_time = time.time()

            # Check max duration
            if self._record_start_time:
                elapsed = time.time() - self._record_start_time
                if elapsed >= self.max_duration:
                    print(f"[ASR] Max duration ({self.max_duration}s) reached, auto-stopping")
                    threading.Thread(target=self._auto_stop_and_transcribe, daemon=True).start()

    def _auto_stop_and_transcribe(self):
        """Auto-stop recording and transcribe when max duration reached."""
        text, confidence = self.stop_and_transcribe()
        if self.on_transcription_complete:
            self.on_transcription_complete(text, confidence)

    def start_stream(self) -> bool:
        """Start the audio input stream."""
        if not AUDIO_AVAILABLE:
            print("[ASR] Audio libraries not available")
            return False
        try:
            self.stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype="int16",
                blocksize=BLOCKSIZE,
                callback=self._audio_callback
            )
            self.stream.start()
            log_debug("Audio stream started")
            return True
        except Exception as e:
            print(f"[ASR] Stream error: {e}")
            log_debug(f"Stream error: {e}")
            if self.on_mic_error:
                self.on_mic_error("Cannot access microphone. Check permissions.")
            return False

    def stop_stream(self):
        """Stop the audio input stream."""
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except:
                pass
            self.stream = None
            log_debug("Audio stream stopped")

    def is_ready(self) -> bool:
        """Check if ready to accept new PTT."""
        return self._ready_for_ptt and not self._recording

    def start_recording(self) -> bool:
        """Start recording audio (PTT pressed or toggle on)."""
        with self._lock:
            if self._recording:
                print("[ASR] Already recording")
                return False

            self._frames = []
            self._record_start_time = time.time()
            self._last_audio_time = time.time()
            self._ready_for_ptt = False

            if not self.stream:
                if not self.start_stream():
                    self._ready_for_ptt = True
                    return False

            self._recording = True
            log_debug(f"Recording started (mode={self.ptt_mode})")
            print(f"[ASR] Recording started (mode={self.ptt_mode}, max={self.max_duration}s)")

            if self.on_recording_start:
                self.on_recording_start()

            # Start mic health monitor
            threading.Thread(target=self._monitor_mic_health, daemon=True).start()

            return True

    def _monitor_mic_health(self):
        """Monitor for dead mic (no audio frames for 2s while recording)."""
        while self._recording:
            time.sleep(0.5)
            if self._recording and self._last_audio_time:
                silence_duration = time.time() - self._last_audio_time
                if silence_duration > 2.0 and len(self._frames) < 5:
                    print("[ASR] No audio frames received for 2s - mic issue?")
                    log_debug("Mic health check failed: no audio frames")
                    if self.on_mic_error:
                        self.on_mic_error("Cannot access microphone. Check permissions.")
                    break

    def stop_recording(self) -> np.ndarray:
        """Stop recording and return raw audio."""
        with self._lock:
            if not self._recording:
                return np.array([], dtype=np.int16)

            self._recording = False
            duration = time.time() - self._record_start_time if self._record_start_time else 0
            log_debug(f"Recording stopped: {duration:.1f}s, {len(self._frames)} frames")
            print(f"[ASR] Recording stopped ({duration:.1f}s, {len(self._frames)} frames)")

            if self.on_recording_stop:
                self.on_recording_stop(duration)

            if not self._frames:
                self._ready_for_ptt = True
                return np.array([], dtype=np.int16)

            audio = np.concatenate(self._frames, axis=0).flatten()
            self._frames = []
            self._record_start_time = None

            return audio

    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._recording

    def get_recording_duration(self) -> float:
        """Get current recording duration in seconds."""
        if self._recording and self._record_start_time:
            return time.time() - self._record_start_time
        return 0.0

    def apply_vad(self, audio: np.ndarray) -> np.ndarray:
        """Apply VAD to trim silence from audio."""
        if self.vad is None or len(audio) == 0:
            return audio
        try:
            frame_size = int(SAMPLE_RATE * 0.03)  # 30ms frames
            voiced = []
            for i in range(0, len(audio) - frame_size, frame_size):
                frame = audio[i:i+frame_size].astype(np.int16).tobytes()
                if len(frame) == frame_size * 2:
                    try:
                        if self.vad.is_speech(frame, SAMPLE_RATE):
                            voiced.append(audio[i:i+frame_size])
                    except:
                        voiced.append(audio[i:i+frame_size])

            if voiced:
                result = np.concatenate(voiced)
                trim_pct = 100 * (1 - len(result) / len(audio))
                print(f"[ASR] VAD trimmed {trim_pct:.0f}% silence")
                return result
            return audio
        except Exception as e:
            print(f"[ASR] VAD error: {e}")
            return audio

    def reduce_noise(self, audio: np.ndarray) -> np.ndarray:
        """Apply noise reduction to audio."""
        if not NR_AVAILABLE or len(audio) == 0:
            return audio
        try:
            audio_float = audio.astype(np.float32) / 32768.0
            reduced = nr.reduce_noise(y=audio_float, sr=SAMPLE_RATE, prop_decrease=0.8)
            return (reduced * 32768).astype(np.int16)
        except Exception as e:
            print(f"[ASR] Noise reduction error: {e}")
            return audio

    def transcribe(self, audio: np.ndarray, preprocess: bool = True) -> tuple:
        """Transcribe audio to text. Returns (text, confidence)."""
        if self.model is None:
            self._ready_for_ptt = True
            return ("", 0.0)

        if len(audio) == 0:
            self._ready_for_ptt = True
            return ("", 0.0)

        # Preprocess
        if preprocess:
            audio = self.apply_vad(audio)
            audio = self.reduce_noise(audio)

        # Minimum audio length check (300ms)
        if len(audio) < SAMPLE_RATE * 0.3:
            print("[ASR] Audio too short after processing")
            self._ready_for_ptt = True
            return ("", 0.0)

        # Save to temp file
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_path = f.name

            audio_float = audio.astype(np.float32) / 32768.0
            sf.write(temp_path, audio_float, SAMPLE_RATE)

            # Transcribe
            start_time = time.time()
            log_debug(f"Transcription started")
            
            segments, info = self.model.transcribe(
                temp_path,
                beam_size=5,
                language="en",
                vad_filter=True,
                word_timestamps=True
            )

            text_parts = []
            confidences = []

            for seg in segments:
                text_parts.append(seg.text)
                seg_conf = 1.0 - getattr(seg, "no_speech_prob", 0.0)
                confidences.append(seg_conf)

            text = " ".join(text_parts).strip()
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            elapsed = time.time() - start_time
            audio_duration = len(audio) / SAMPLE_RATE
            
            print(f"[ASR] Transcribed in {elapsed:.1f}s: '{text[:50]}...' (conf={avg_confidence:.2f})")
            log_debug(f"Transcription completed: {elapsed:.1f}s, conf={avg_confidence:.2f}")
            log_improvement(f"Transcription: {elapsed:.1f}s for {audio_duration:.1f}s audio, model={self.model_name}, device={self.device}")

            # Log to file
            stt_logger.info(f"duration={audio_duration:.1f}s | conf={avg_confidence:.2f} | text={text}")

            if temp_path:
                try:
                    os.unlink(temp_path)
                except:
                    pass

            return (text, avg_confidence)

        except Exception as e:
            print(f"[ASR] Transcription error: {e}")
            log_debug(f"Transcription error: {e}")
            if temp_path:
                try:
                    os.unlink(temp_path)
                except:
                    pass
            return ("", 0.0)
        finally:
            self._ready_for_ptt = True

    def stop_and_transcribe(self) -> tuple:
        """Stop recording and transcribe in one call."""
        audio = self.stop_recording()

        if len(audio) == 0:
            self._ready_for_ptt = True
            return ("", 0.0)

        text, confidence = self.transcribe(audio)

        # Handle low confidence
        if confidence < self.confidence_threshold and text:
            print(f"[ASR] Low confidence ({confidence:.2f} < {self.confidence_threshold})")
            if self.on_low_confidence:
                self.on_low_confidence(text, confidence)

        # Handle empty transcription
        if not text.strip():
            print("[ASR] Empty transcription")

        return (text, confidence)

    def toggle_recording(self) -> bool:
        """Toggle recording state (for toggle PTT mode)."""
        if self._recording:
            return False
        else:
            return self.start_recording()


# Singleton instance
_engine = None

def get_engine() -> ASREngine:
    """Get or create singleton ASR engine."""
    global _engine
    if _engine is None:
        _engine = ASREngine()
    return _engine

def reinitialize_engine():
    """Reinitialize the ASR engine."""
    global _engine
    if _engine:
        _engine.stop_stream()
    _engine = ASREngine()
    return _engine


if __name__ == "__main__":
    print("=" * 50)
    print("ASR Engine Test")
    print("=" * 50)

    engine = ASREngine()

    print("\nRecording for 5 seconds...")
    engine.start_recording()
    time.sleep(5)

    text, conf = engine.stop_and_transcribe()
    print(f"\nResult: '{text}'")
    print(f"Confidence: {conf:.2f}")

    engine.stop_stream()
    print("\nDone!")
