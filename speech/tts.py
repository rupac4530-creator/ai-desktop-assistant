import os
import requests
import tempfile
import subprocess

ELEVEN_KEY = os.getenv('ELEVENLABS_API_KEY')
VOICE_ID = os.getenv('ELEVENLABS_VOICE_ID','21m00Tcm4TlvDq8ikWAM')

def speak_text(text, lang='en'):
    if not ELEVEN_KEY:
        # fallback: simple PowerShell speech
        ps = f"Add-Type –AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Speak(\"{text}\")"
        subprocess.Popen(['powershell','-Command',ps])
        return

    url = f'https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}'
    headers = {'xi-api-key': ELEVEN_KEY, 'Content-Type':'application/json'}
    payload = {'text': text, 'voice': 'alloy', 'model': 'eleven_multilingual_v1'}
    r = requests.post(url, json=payload, headers=headers, stream=True)
    if r.status_code != 200:
        return
    fd, path = tempfile.mkstemp(suffix='.wav')
    with os.fdopen(fd, 'wb') as f:
        for chunk in r.iter_content(1024):
            f.write(chunk)
    # play file synchronously
    subprocess.run(['powershell','-c',f'(New-Object Media.SoundPlayer \"{path}\").PlaySync();'])
    try:
        os.remove(path)
    except: pass
