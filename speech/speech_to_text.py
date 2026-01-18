import pyaudio
import wave
import os
import threading
from faster_whisper import WhisperModel

TEMP_AUDIO = os.path.join(os.path.dirname(__file__), "temp_audio.wav")

class SpeechToText:
    def __init__(self, model_size="base"):
        print("Loading Whisper model (this may take a moment on first run)...")
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        print("Whisper model loaded!")

        # PTT state
        self._recording = False
        self._frames = []
        self._stream = None
        self._pya = None
        self._lock = threading.Lock()
        self._record_thread = None
        self._stop_event = threading.Event()

        # Audio settings
        self._chunk = 1024
        self._rate = 16000
        self._channels = 1
        self._format = pyaudio.paInt16
        
        # Test microphone on init
        self._test_microphone()

    def _test_microphone(self):
        """Test that microphone is accessible."""
        try:
            p = pyaudio.PyAudio()
            default = p.get_default_input_device_info()
            print(f"[STT] Default mic: {default['name']} (index {default['index']})")
            p.terminate()
        except Exception as e:
            print(f"[STT] WARNING - Microphone test failed: {e}")

    def start_recording(self):
        """Start continuous recording in background thread."""
        with self._lock:
            if self._recording:
                print("[STT] Already recording!")
                return False

            self._frames = []
            self._stop_event.clear()
            
            try:
                self._pya = pyaudio.PyAudio()
                self._stream = self._pya.open(
                    format=self._format,
                    channels=self._channels,
                    rate=self._rate,
                    input=True,
                    frames_per_buffer=self._chunk
                )
                self._recording = True

                # Start background thread to continuously capture audio
                self._record_thread = threading.Thread(target=self._capture_loop, daemon=True)
                self._record_thread.start()

                print("[STT] Recording started...")
                return True
            except Exception as e:
                print(f"[STT] Failed to start recording: {e}")
                if self._pya:
                    try:
                        self._pya.terminate()
                    except:
                        pass
                return False

    def _capture_loop(self):
        """Continuously capture audio frames while recording."""
        frame_count = 0
        while not self._stop_event.is_set():
            try:
                data = self._stream.read(self._chunk, exception_on_overflow=False)
                with self._lock:
                    if self._recording:
                        self._frames.append(data)
                        frame_count += 1
            except Exception as e:
                print(f"[STT] Capture error: {e}")
                break
        print(f"[STT] Capture loop ended, captured {frame_count} frames")

    def stop_recording_and_transcribe(self):
        """Stop recording and transcribe captured audio."""
        frames_copy = []

        with self._lock:
            if not self._recording:
                print("[STT] Not recording!")
                return ""

            # Signal stop and wait for thread
            self._stop_event.set()
            self._recording = False
            frames_copy = self._frames.copy()
            print(f"[STT] Stopping recording, got {len(frames_copy)} frames")

        # Wait for capture thread to finish
        if self._record_thread:
            self._record_thread.join(timeout=1.0)

        # Clean up stream
        try:
            if self._stream:
                self._stream.stop_stream()
                self._stream.close()
            if self._pya:
                self._pya.terminate()
        except Exception as e:
            print(f"[STT] Cleanup error: {e}")

        # Write captured audio to file
        if len(frames_copy) < 5:
            print(f"[STT] Too few frames ({len(frames_copy)}), need at least 5")
            return ""
            
        try:
            wf = wave.open(TEMP_AUDIO, 'wb')
            wf.setnchannels(self._channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self._rate)
            wf.writeframes(b''.join(frames_copy))
            wf.close()
            
            file_size = os.path.getsize(TEMP_AUDIO)
            duration = len(frames_copy) * self._chunk / self._rate
            print(f"[STT] Saved {file_size} bytes ({duration:.1f}s audio), transcribing...")
        except Exception as e:
            print(f"[STT] Write error: {e}")
            return ""

        return self.transcribe()

    def record_audio(self, duration=5):
        """Synchronous recording for legacy compatibility."""
        print(f"Recording for {duration} seconds...")
        p = pyaudio.PyAudio()
        stream = p.open(
            format=self._format,
            channels=self._channels,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk
        )
        frames = []
        for _ in range(0, int(self._rate / self._chunk * duration)):
            data = stream.read(self._chunk)
            frames.append(data)
        stream.stop_stream()
        stream.close()
        p.terminate()

        wf = wave.open(TEMP_AUDIO, 'wb')
        wf.setnchannels(self._channels)
        wf.setsampwidth(p.get_sample_size(self._format))
        wf.setframerate(self._rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        print("Recording complete!")

    def transcribe(self, path=None):
        """Transcribe audio file using Whisper."""
        if path is None:
            path = TEMP_AUDIO
        
        if not os.path.exists(path):
            print(f"[STT] Audio file not found: {path}")
            return ""
            
        try:
            segments, info = self.model.transcribe(path, beam_size=5)
            text = " ".join([segment.text for segment in segments])
            result = text.strip()
            print(f"[STT] Transcribed: '{result}'")
            return result
        except Exception as e:
            print(f"[STT] Transcription error: {e}")
            return ""

    def listen_and_transcribe(self, duration=5):
        """Legacy method: record for fixed duration and transcribe."""
        self.record_audio(duration)
        return self.transcribe()