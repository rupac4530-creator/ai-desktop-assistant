# E:\ai_desktop_assistant\tools\calibrate_mic.py
"""
Microphone calibration tool.
Measures ambient noise level and sets optimal VAD parameters.
Saves results to config/mic.json
"""

import os
import sys
import json
import time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import sounddevice as sd
except ImportError:
    print("ERROR: sounddevice not installed. Run: pip install sounddevice")
    sys.exit(1)

SAMPLE_RATE = 16000
DURATION = 3  # seconds to measure
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "mic.json")


def measure_ambient_noise(duration: float = 3.0) -> dict:
    """
    Measure ambient noise level.
    
    Returns:
        Dict with rms, peak, and recommended VAD settings
    """
    print(f"\n🎤 Measuring ambient noise for {duration} seconds...")
    print("   Please remain SILENT during measurement.\n")
    
    time.sleep(1)  # Give user time to be quiet
    
    # Record ambient audio
    audio = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='int16')
    sd.wait()
    
    audio = audio.flatten().astype(np.float32)
    
    # Calculate metrics
    rms = np.sqrt(np.mean(audio ** 2))
    peak = np.max(np.abs(audio))
    
    # Determine VAD aggressiveness based on noise level
    # Higher noise = more aggressive VAD filtering
    if rms < 500:
        vad_level = 1  # Quiet room
        noise_desc = "Very quiet"
    elif rms < 1500:
        vad_level = 2  # Normal room
        noise_desc = "Normal"
    elif rms < 3000:
        vad_level = 2  # Somewhat noisy
        noise_desc = "Moderate noise"
    else:
        vad_level = 3  # Noisy environment
        noise_desc = "Noisy"
    
    return {
        "ambient_rms": float(rms),
        "ambient_peak": float(peak),
        "noise_level": noise_desc,
        "vad_aggressiveness": vad_level,
        "calibrated_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }


def test_speech_detection(duration: float = 3.0) -> dict:
    """
    Test speech detection to measure typical speech level.
    """
    print(f"\n🗣️ Now SPEAK NORMALLY for {duration} seconds...")
    print("   Say something like: 'Hello, this is a test of the microphone.'\n")
    
    time.sleep(0.5)
    
    audio = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='int16')
    sd.wait()
    
    audio = audio.flatten().astype(np.float32)
    
    rms = np.sqrt(np.mean(audio ** 2))
    peak = np.max(np.abs(audio))
    
    return {
        "speech_rms": float(rms),
        "speech_peak": float(peak)
    }


def calibrate():
    """Run full calibration sequence."""
    print("=" * 50)
    print("🎙️  MICROPHONE CALIBRATION")
    print("=" * 50)
    
    # List available devices
    print("\nAvailable audio devices:")
    devices = sd.query_devices()
    for i, d in enumerate(devices):
        if d['max_input_channels'] > 0:
            marker = " <-- DEFAULT" if i == sd.default.device[0] else ""
            print(f"  [{i}] {d['name']}{marker}")
    
    print(f"\nUsing default input device: {sd.query_devices(sd.default.device[0])['name']}")
    
    # Measure ambient noise
    ambient = measure_ambient_noise(DURATION)
    print(f"\n📊 Ambient Noise Results:")
    print(f"   RMS Level: {ambient['ambient_rms']:.0f}")
    print(f"   Peak Level: {ambient['ambient_peak']:.0f}")
    print(f"   Environment: {ambient['noise_level']}")
    print(f"   Recommended VAD Level: {ambient['vad_aggressiveness']}")
    
    # Test speech
    speech = test_speech_detection(DURATION)
    print(f"\n📊 Speech Detection Results:")
    print(f"   RMS Level: {speech['speech_rms']:.0f}")
    print(f"   Peak Level: {speech['speech_peak']:.0f}")
    
    # Calculate SNR
    if ambient['ambient_rms'] > 0:
        snr = 20 * np.log10(speech['speech_rms'] / ambient['ambient_rms'])
        print(f"   Signal-to-Noise Ratio: {snr:.1f} dB")
        
        if snr < 10:
            print("\n⚠️  Warning: Low SNR. Consider using a better microphone or quieter environment.")
    
    # Combine results
    config = {
        **ambient,
        **speech,
        "sample_rate": SAMPLE_RATE,
        "input_device": sd.query_devices(sd.default.device[0])['name']
    }
    
    # Save config
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n✅ Calibration saved to: {CONFIG_PATH}")
    print("\nConfiguration:")
    print(json.dumps(config, indent=2))
    
    return config


if __name__ == "__main__":
    try:
        calibrate()
    except KeyboardInterrupt:
        print("\n\nCalibration cancelled.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
