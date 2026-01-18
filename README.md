# AI Desktop Assistant

A voice-controlled AI assistant with visible avatar, built with Python.

## Features

- Voice input (speech-to-text via Whisper)
- AI brain (GPT-4 via OpenAI API)
- Voice output (text-to-speech via ElevenLabs)
- System control (open apps)
- Memory management
- Avatar animations via OSC (VTube Studio)

## Setup

1. Install Python (Miniconda installed on E:\miniconda)
2. Set environment variables:
   - OPENAI_API_KEY
   - ELEVENLABS_API_KEY
3. Run `run_assistant.bat`

## Avatar Setup (VTube Studio)

1. Install VTube Studio
2. Enable OSC in Settings > OSC > Enable OSC, Port 9000
3. Create parameters for animations (e.g., dance, happy)
4. For lip sync: Use VB-Cable to route audio to virtual mic that VTube Studio listens to.

## Usage

Say commands like:
- "Open YouTube"
- "Dance"
- "Hello"

The AI will respond and animate.