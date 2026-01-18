# diagnostics.py — quick tests for OpenAI and ElevenLabs TTS
# Run: python diagnostics.py

import os
from dotenv import load_dotenv
load_dotenv()

def test_openai():
    print("[1] Testing OpenAI...")
    key = os.getenv("OPENAI_API_KEY")
    if not key or "REPLACE" in key:
        print("  Skipped: OPENAI_API_KEY not set or placeholder.")
        return
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say hello in one word."}],
            max_tokens=5
        )
        print(f"  OpenAI OK: {r.choices[0].message.content.strip()}")
    except Exception as e:
        print(f"  OpenAI error: {e}")

def test_elevenlabs():
    print("[2] Testing ElevenLabs TTS...")
    key = os.getenv("ELEVENLABS_API_KEY")
    if not key or "REPLACE" in key:
        print("  Skipped: ELEVENLABS_API_KEY not set or placeholder.")
        return
    try:
        import requests
        voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {"xi-api-key": key, "Content-Type": "application/json"}
        payload = {"text": "Hello", "model_id": "eleven_multilingual_v1"}
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        if r.status_code == 200 and len(r.content) > 1000:
            print(f"  ElevenLabs OK: received {len(r.content)} bytes audio.")
        else:
            print(f"  ElevenLabs returned status {r.status_code}")
    except Exception as e:
        print(f"  ElevenLabs error: {e}")

def test_vb_cable():
    print("[3] Checking VB-Cable audio device...")
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        found = [d['name'] for d in devices if 'cable' in d['name'].lower()]
        if found:
            print(f"  VB-Cable devices found: {found}")
        else:
            print("  VB-Cable not detected. Install from https://vb-audio.com/Cable/")
    except Exception as e:
        print(f"  sounddevice error: {e}")

if __name__ == "__main__":
    print("== AI Desktop Assistant Diagnostics ==\n")
    test_openai()
    test_elevenlabs()
    test_vb_cable()
    print("\n== Done ==")
