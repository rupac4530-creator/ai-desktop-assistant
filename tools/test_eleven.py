"""test_eleven.py — validate ElevenLabs API key and model availability
Run: python tools/test_eleven.py
"""

import os
from dotenv import load_dotenv
load_dotenv()

key = os.getenv("ELEVENLABS_API_KEY")
if not key or "REPLACE" in key:
    print("ELEVENLABS_API_KEY not set or still placeholder in .env")
    exit(1)

import requests
# Use a voice ID in the URL and request a model in the payload. Update voice_id if needed.
voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
model = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
headers = {"xi-api-key": key, "Content-Type": "application/json"}
payload = {"text": "Hello, this is a test from your assistant.", "model": model}

print(f"Testing ElevenLabs with key prefix: {key[:8]}, voice: {voice_id}, model: {model}...")
r = requests.post(url, json=payload, headers=headers, timeout=15)
print(f"Status: {r.status_code}")

if r.status_code == 200:
    print(f"ElevenLabs TTS OK — received {len(r.content)} bytes audio.")
    with open("test_tts.bin", "wb") as f:
        f.write(r.content)
    print("Saved to test_tts.bin")
else:
    print(f"ElevenLabs error response:\n{r.text[:1000]}")
# test_eleven.py — validate ElevenLabs API key
# Run: python tools/test_eleven.py

import os
from dotenv import load_dotenv
load_dotenv()

key = os.getenv("ELEVENLABS_API_KEY")
if not key or "REPLACE" in key:
    print("ELEVENLABS_API_KEY not set or still placeholder in .env")
    exit(1)

import requests
url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"
headers = {"xi-api-key": key, "Content-Type": "application/json"}
payload = {"text": "Hello, this is a test from your assistant.", "model_id": "eleven_multilingual_v1"}

print(f"Testing ElevenLabs with key: {key[:8]}...")
r = requests.post(url, json=payload, headers=headers, timeout=15)
print(f"Status: {r.status_code}")

if r.status_code == 200:
    print(f"ElevenLabs TTS OK — received {len(r.content)} bytes audio.")
    # Optionally save and play
    with open("test_tts.mp3", "wb") as f:
        f.write(r.content)
    print("Saved to test_tts.mp3")
else:
    print(f"ElevenLabs error response:\n{r.text[:500]}")
