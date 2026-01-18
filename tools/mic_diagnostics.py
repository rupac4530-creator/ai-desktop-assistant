#!/usr/bin/env python3
"""
Microphone Diagnostics Tool - Comprehensive audio device testing.
Probes all audio input devices and finds a working one.
"""

import sys
import os
import json
import time
import wave
import numpy as np
from pathlib import Path
from datetime import datetime

# Add project root to path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
LOGS_DIR = ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Log file for this run
LOG_FILE = LOGS_DIR / "self_heal_agent_run.log"


def log(msg: str):
    """Log to file and console."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def step_2_capture_device_list():
    """Step 2: Capture full device list & status."""
    log("=== STEP 2: Capture Device List ===")
    
    try:
        import sounddevice as sd
        
        devices = sd.query_devices()
        default_input = sd.default.device[0]
        default_output = sd.default.device[1]
        
        device_info = {
            "timestamp": datetime.now().isoformat(),
            "default_input_index": default_input,
            "default_output_index": default_output,
            "devices": [],
        }
        
        for i, dev in enumerate(devices):
            device_info["devices"].append({
                "index": i,
                "name": dev["name"],
                "max_input_channels": dev["max_input_channels"],
                "max_output_channels": dev["max_output_channels"],
                "default_samplerate": dev["default_samplerate"],
                "is_default_input": i == default_input,
                "is_input": dev["max_input_channels"] > 0,
            })
        
        # Save to JSON
        with open(LOGS_DIR / "device_list.json", "w", encoding="utf-8") as f:
            json.dump(device_info, f, indent=2)
        
        log(f"Found {len(devices)} audio devices")
        log(f"Default input device: {default_input}")
        
        # List input devices
        input_devices = [d for d in device_info["devices"] if d["is_input"]]
        log(f"Input devices: {len(input_devices)}")
        for d in input_devices:
            marker = " [DEFAULT]" if d["is_default_input"] else ""
            log(f"  [{d['index']}] {d['name']}{marker}")
        
        return device_info
        
    except Exception as e:
        log(f"ERROR in step 2: {e}")
        return None


def step_3_probe_devices(device_info: dict):
    """Step 3: Try programmatic mic test on each candidate device."""
    log("=== STEP 3: Probe Each Input Device ===")
    
    import sounddevice as sd
    
    probe_results = []
    working_device = None
    
    input_devices = [d for d in device_info["devices"] if d["is_input"]]
    
    for dev in input_devices:
        idx = dev["index"]
        name = dev["name"]
        log(f"Probing device [{idx}]: {name}")
        
        result = {
            "index": idx,
            "name": name,
            "ok": False,
            "frames": 0,
            "rms": 0.0,
            "error": None,
            "sample_rates_tried": [],
        }
        
        # Try multiple sample rates
        sample_rates = [16000, 22050, 44100, 48000]
        
        for sr in sample_rates:
            try:
                duration = 1.5  # seconds
                log(f"  Trying {sr}Hz...")
                
                # Record
                recording = sd.rec(
                    int(duration * sr),
                    samplerate=sr,
                    channels=1,
                    dtype='int16',
                    device=idx,
                )
                sd.wait()
                
                # Analyze
                frames = len(recording)
                rms = np.sqrt(np.mean(recording.astype(np.float32) ** 2))
                
                result["sample_rates_tried"].append({
                    "rate": sr,
                    "frames": frames,
                    "rms": float(rms),
                })
                
                log(f"    Frames: {frames}, RMS: {rms:.1f}")
                
                # Check if valid audio (frames > 0 and RMS > noise threshold)
                if frames > 0 and rms > 5:  # Lower threshold for quiet rooms
                    result["ok"] = True
                    result["frames"] = frames
                    result["rms"] = float(rms)
                    result["working_sample_rate"] = sr
                    
                    if working_device is None:
                        working_device = {
                            "index": idx,
                            "name": name,
                            "sample_rate": sr,
                            "rms": float(rms),
                        }
                        log(f"  âœ“ Device [{idx}] works at {sr}Hz (RMS: {rms:.1f})")
                    break
                    
            except Exception as e:
                result["sample_rates_tried"].append({
                    "rate": sr,
                    "error": str(e),
                })
                log(f"    Error at {sr}Hz: {e}")
        
        if not result["ok"]:
            result["error"] = "No valid audio captured at any sample rate"
            log(f"  âœ— Device [{idx}] failed")
        
        probe_results.append(result)
        
        # Write incrementally
        with open(LOGS_DIR / "device_probe.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(result) + "\n")
    
    # Summary
    log(f"Probe complete: {sum(1 for r in probe_results if r['ok'])}/{len(probe_results)} devices working")
    
    return probe_results, working_device


def step_4_fallback_attempts():
    """Step 4: Fallback if no device reports OK."""
    log("=== STEP 4: Fallback Attempts ===")
    
    try:
        import sounddevice as sd
        
        # Try with different parameters
        fallback_configs = [
            {"samplerate": 16000, "channels": 1, "dtype": "int16"},
            {"samplerate": 22050, "channels": 1, "dtype": "int16"},
            {"samplerate": 48000, "channels": 1, "dtype": "int16"},
            {"samplerate": 16000, "channels": 1, "dtype": "float32"},
        ]
        
        for config in fallback_configs:
            log(f"  Trying fallback config: {config}")
            try:
                rec = sd.rec(int(1.5 * config["samplerate"]), **config)
                sd.wait()
                rms = np.sqrt(np.mean(rec.astype(np.float32) ** 2))
                if rms > 5:
                    log(f"  âœ“ Fallback worked: RMS={rms:.1f}")
                    return {"ok": True, "config": config, "rms": float(rms)}
            except Exception as e:
                log(f"    Failed: {e}")
        
        return {"ok": False, "error": "All fallback attempts failed"}
        
    except Exception as e:
        log(f"ERROR in fallback: {e}")
        return {"ok": False, "error": str(e)}


def step_5_check_permissions():
    """Step 5: Check microphone permissions."""
    log("=== STEP 5: Check Permissions ===")
    
    # On Windows, we can't directly check UWP permissions from Python
    # But we can try to record and check the error
    
    try:
        import sounddevice as sd
        
        # Quick test
        rec = sd.rec(1000, samplerate=16000, channels=1, dtype='int16')
        sd.wait()
        
        if len(rec) > 0:
            log("  Microphone access appears OK")
            return {"permission_ok": True}
        else:
            log("  WARNING: Recording returned 0 frames - possible permission issue")
            return {"permission_ok": False, "hint": "Check Windows Settings > Privacy > Microphone"}
            
    except Exception as e:
        error_str = str(e).lower()
        if "permission" in error_str or "access" in error_str or "denied" in error_str:
            log(f"  PERMISSION ERROR: {e}")
            return {"permission_ok": False, "error": str(e)}
        else:
            log(f"  Other error (not permission): {e}")
            return {"permission_ok": True, "other_error": str(e)}


def step_6_update_config(working_device: dict):
    """Step 6: Update .env with working device."""
    log("=== STEP 6: Update Configuration ===")
    
    if not working_device:
        log("  No working device to configure")
        return False
    
    env_file = ROOT / ".env"
    env_content = env_file.read_text(encoding="utf-8") if env_file.exists() else ""
    
    # Update or add MIC_DEVICE_INDEX
    idx = working_device["index"]
    sr = working_device.get("sample_rate", 16000)
    
    if "MIC_DEVICE_INDEX" in env_content:
        import re
        env_content = re.sub(r"MIC_DEVICE_INDEX=\d+", f"MIC_DEVICE_INDEX={idx}", env_content)
    else:
        env_content += f"\nMIC_DEVICE_INDEX={idx}"
    
    if "MIC_SAMPLE_RATE" in env_content:
        import re
        env_content = re.sub(r"MIC_SAMPLE_RATE=\d+", f"MIC_SAMPLE_RATE={sr}", env_content)
    else:
        env_content += f"\nMIC_SAMPLE_RATE={sr}"
    
    env_file.write_text(env_content.strip() + "\n", encoding="utf-8")
    log(f"  Set MIC_DEVICE_INDEX={idx}, MIC_SAMPLE_RATE={sr}")
    
    # Also save to state.json for persistence
    state_file = ROOT / "core" / "state.json"
    state = {}
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text())
        except:
            pass
    
    state["mic_device_index"] = idx
    state["mic_sample_rate"] = sr
    state["mic_device_name"] = working_device["name"]
    state["mic_configured_at"] = datetime.now().isoformat()
    
    state_file.write_text(json.dumps(state, indent=2))
    log(f"  Saved to core/state.json")
    
    return True


def step_7_test_capture():
    """Step 7: Test actual capture with configured device."""
    log("=== STEP 7: Test Audio Capture ===")
    
    try:
        import sounddevice as sd
        
        # Load config
        env_file = ROOT / ".env"
        env_content = env_file.read_text() if env_file.exists() else ""
        
        # Parse MIC_DEVICE_INDEX
        import re
        match = re.search(r"MIC_DEVICE_INDEX=(\d+)", env_content)
        device_idx = int(match.group(1)) if match else None
        
        match = re.search(r"MIC_SAMPLE_RATE=(\d+)", env_content)
        sample_rate = int(match.group(1)) if match else 16000
        
        log(f"  Testing device {device_idx} at {sample_rate}Hz")
        
        # Record 3 seconds
        duration = 3
        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype='int16',
            device=device_idx,
        )
        sd.wait()
        
        # Save WAV
        wav_path = LOGS_DIR / "test_mic.wav"
        with wave.open(str(wav_path), 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(recording.tobytes())
        
        rms = np.sqrt(np.mean(recording.astype(np.float32) ** 2))
        log(f"  Saved {wav_path} ({len(recording)} frames, RMS: {rms:.1f})")
        
        return {
            "ok": rms > 5,
            "frames": len(recording),
            "rms": float(rms),
            "wav_path": str(wav_path),
        }
        
    except Exception as e:
        log(f"  ERROR: {e}")
        return {"ok": False, "error": str(e)}


def step_8_add_circuit_breaker():
    """Step 8: Add circuit breaker to prevent endless loops."""
    log("=== STEP 8: Circuit Breaker Configuration ===")
    
    # This is handled by the .env settings already
    # But we can add a state flag
    state_file = ROOT / "core" / "state.json"
    state = {}
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text())
        except:
            pass
    
    state["circuit_breaker"] = {
        "mic_repair_attempts": 0,
        "max_attempts": 3,
        "cooldown_minutes": 10,
        "last_attempt": None,
    }
    
    state_file.write_text(json.dumps(state, indent=2))
    log("  Circuit breaker state initialized")
    return True


def run_full_diagnostics():
    """Run all diagnostic steps."""
    log("=" * 60)
    log("MICROPHONE DIAGNOSTICS - Starting")
    log("=" * 60)
    
    # Clear previous probe results
    probe_file = LOGS_DIR / "device_probe.jsonl"
    if probe_file.exists():
        probe_file.unlink()
    
    # Step 2: Get device list
    device_info = step_2_capture_device_list()
    if not device_info:
        log("FATAL: Could not enumerate audio devices")
        return {"status": "FAILED", "error": "No audio devices found"}
    
    # Step 3: Probe devices
    probe_results, working_device = step_3_probe_devices(device_info)
    
    # Step 4: Fallback if needed
    if not working_device:
        log("No working device found, trying fallbacks...")
        fallback = step_4_fallback_attempts()
        if not fallback.get("ok"):
            # Step 5: Check permissions
            perm = step_5_check_permissions()
            if not perm.get("permission_ok"):
                log("MICROPHONE PERMISSION ISSUE DETECTED")
                log("Please open: Settings > Privacy > Microphone")
                log("Enable 'Allow apps to access your microphone'")
    
    # Step 6: Update config if we have a working device
    if working_device:
        step_6_update_config(working_device)
        
        # Step 7: Test capture
        test_result = step_7_test_capture()
        
        # Step 8: Circuit breaker
        step_8_add_circuit_breaker()
        
        if test_result.get("ok"):
            log("=" * 60)
            log("MIC_FIX=SUCCESS")
            log(f"Working device: [{working_device['index']}] {working_device['name']}")
            log("=" * 60)
            return {
                "status": "SUCCESS",
                "device": working_device,
                "test": test_result,
            }
    
    log("=" * 60)
    log("MIC_FIX=FAILED - No working microphone found")
    log("Please check:")
    log("  1. Windows Settings > Privacy > Microphone")
    log("  2. Close other apps using microphone (Teams, Zoom, etc.)")
    log("  3. Check hardware connection")
    log("=" * 60)
    
    return {
        "status": "FAILED",
        "devices_probed": len(probe_results),
        "working_devices": 0,
    }


if __name__ == "__main__":
    # Ensure sounddevice is installed
    try:
        import sounddevice
    except ImportError:
        print("Installing sounddevice...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "sounddevice", "-q"])
        import sounddevice
    
    result = run_full_diagnostics()
    print("\n" + "=" * 60)
    print("RESULT:", json.dumps(result, indent=2))

