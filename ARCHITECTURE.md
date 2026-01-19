# System Architecture

High-level architecture and component documentation for the AI Desktop Assistant.

---

## 🏗️ System Overview

```
┌────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  Keyboard    │  │    Voice     │  │    Avatar    │  │   System     │   │
│  │  Hotkeys     │  │   Commands   │  │   Display    │  │   Tray       │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
└─────────┼─────────────────┼─────────────────┼─────────────────┼───────────┘
          │                 │                 │                 │
          ▼                 ▼                 ▼                 ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                           MAIN CONTROLLER                                   │
│                        core/main_controller.py                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Event Loop  │  State Manager  │  Component Orchestration           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────┘
          │                 │                 │                 │
          ▼                 ▼                 ▼                 ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│    SPEECH       │ │     BRAIN       │ │    AVATAR       │ │   AUTOMATION    │
│  ┌───────────┐  │ │  ┌───────────┐  │ │  ┌───────────┐  │ │  ┌───────────┐  │
│  │    ASR    │  │ │  │  Ollama   │  │ │  │  Live2D   │  │ │  │ Keyboard  │  │
│  │ (Whisper) │  │ │  │   LLM     │  │ │  │  Render   │  │ │  │  Control  │  │
│  ├───────────┤  │ │  ├───────────┤  │ │  ├───────────┤  │ │  ├───────────┤  │
│  │    TTS    │  │ │  │  Memory   │  │ │  │  Emotion  │  │ │  │  Mouse    │  │
│  │  (Piper)  │  │ │  │  Store    │  │ │  │  Engine   │  │ │  │  Control  │  │
│  ├───────────┤  │ │  ├───────────┤  │ │  ├───────────┤  │ │  ├───────────┤  │
│  │    VAD    │  │ │  │  Intent   │  │ │  │  Lip      │  │ │  │  App      │  │
│  │ (WebRTC)  │  │ │  │  Parser   │  │ │  │  Sync     │  │ │  │  Launch   │  │
│  └───────────┘  │ │  └───────────┘  │ │  └───────────┘  │ │  └───────────┘  │
└─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘
          │                 │                 │                 │
          ▼                 ▼                 ▼                 ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                          SELF-HEALING LAYER                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Watchdog   │  │   Repair     │  │  Git Helper  │  │   Circuit    │   │
│  │   Monitor    │  │   Engine     │  │  (Rollback)  │  │   Breaker    │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Component Details

### 1. Speech Module (`speech/`)

#### ASR - Automatic Speech Recognition
- **File**: `speech/asr.py`
- **Engine**: Faster-Whisper (CTranslate2)
- **Models**: tiny, base, small, medium, large-v2
- **Features**:
  - CUDA acceleration (GPU)
  - CPU fallback
  - Voice Activity Detection (WebRTC VAD)
  - Noise reduction
  - Confidence scoring

#### TTS - Text-to-Speech
- **File**: `speech/local_tts.py`
- **Engine**: Piper (ONNX neural voices)
- **Features**:
  - Multiple voice models
  - Adjustable speed/pitch
  - Low latency streaming

### 2. Brain Module (`brain/`)

#### LLM Integration
- **File**: `brain/ollama_client.py`
- **Backend**: Ollama (local)
- **Models Supported**:
  - Mistral 7B (default)
  - LLaMA 3
  - CodeLlama (for coding tasks)
- **Features**:
  - Context memory
  - Intent classification
  - Multi-turn conversations

#### Memory System
- **File**: `memory/`
- **Storage**: JSON + SQLite
- **Features**:
  - Conversation history
  - User preferences
  - Task context

### 3. Avatar Module (`avatar/`)

#### Live2D Renderer
- **File**: `avatar/live2d_widget.py`
- **Features**:
  - Real-time animation
  - Emotion expression
  - Lip sync with TTS
  - Always-on-top overlay

#### Emotion Engine
- **File**: `avatar/emotion_engine.py`
- **Emotions**: happy, sad, surprised, thinking, speaking
- **Trigger**: Sentiment analysis of responses

### 4. Automation Module (`automation/`)

#### Desktop Control
- **File**: `automation/desktop_control.py`
- **Capabilities**:
  - Keyboard simulation
  - Mouse control
  - Window management
  - Application launching

#### Browser Automation
- **File**: `automation/browser_control.py`
- **Engine**: Playwright/Selenium
- **Features**:
  - Web navigation
  - Form filling
  - Content extraction

### 5. Self-Healing Layer (`core/`)

#### Watchdog
- **File**: `core/watchdog.py`
- **Function**: Monitors system health
- **Checks**:
  - Component heartbeats
  - Error rate thresholds
  - Resource usage

#### Repair Engine
- **File**: `core/repair_engine.py`
- **Actions**:
  - Restart failed components
  - Rebind hotkeys
  - Reset audio devices
  - Clear stuck processes

#### Git Helper
- **File**: `core/git_helper.py`
- **Features**:
  - Automatic branching
  - Commit with semantic messages
  - Rollback capability
  - Change diffing

#### Circuit Breaker
- **Function**: Prevents repair loops
- **Limits**:
  - 3 repairs per 10 minutes
  - Auto-disable on repeated failures

### 6. Autonomous Coder (`core/autonomous_coder.py`)

- **Function**: Self-improvement capability
- **Features**:
  - Analyze and fix bugs
  - Implement features from descriptions
  - Test validation before commit
  - Git-backed rollback on failure

---

## 🔄 Data Flow

### Voice Command Flow

```
User speaks → Microphone → ASR (Whisper) → Text
    ↓
Intent Parser → Brain (LLM) → Response
    ↓
TTS (Piper) → Audio → Speaker
    ↓
Avatar → Emotion + Lip Sync → Display
```

### Automation Flow

```
Voice Command → Intent: "open YouTube"
    ↓
Automation Engine → Browser Control
    ↓
Execute Action → Open browser, navigate
    ↓
Confirmation → TTS: "YouTube is now open"
```

### Self-Healing Flow

```
Error Detected → Watchdog Alert
    ↓
Repair Engine → Select Action
    ↓
Create Git Branch → Apply Fix
    ↓
Run Tests → Pass? → Merge & Continue
           → Fail? → Rollback & Log
```

---

## 📁 Directory Structure

```
ai_desktop_assistant/
├── core/                    # Main application logic
│   ├── main_controller.py   # Entry point
│   ├── watchdog.py          # Health monitoring
│   ├── repair_engine.py     # Self-healing actions
│   ├── autonomous_coder.py  # Self-improvement
│   ├── git_helper.py        # Git operations
│   └── state.json           # Runtime state
├── speech/                  # Voice I/O
│   ├── asr.py              # Speech recognition
│   └── local_tts.py        # Text-to-speech
├── brain/                   # AI reasoning
│   ├── ollama_client.py    # LLM interface
│   └── intent_parser.py    # Command parsing
├── avatar/                  # Visual representation
│   ├── live2d_widget.py    # Avatar display
│   └── emotion_engine.py   # Expression control
├── automation/              # Desktop control
│   ├── desktop_control.py  # System automation
│   └── browser_control.py  # Web automation
├── ui/                      # User interface
│   ├── keyboard.py         # Hotkey handling
│   └── system_tray.py      # Tray icon
├── config/                  # Configuration
│   └── agent_directives.py # AI behavior rules
├── tools/                   # Utilities
│   ├── mic_diagnostics.py  # Audio testing
│   └── test_core_smoke.py  # Unit tests
├── logs/                    # Runtime logs
├── models/                  # AI models
├── .env                     # Environment config
└── requirements.txt         # Dependencies
```

---

## 🔧 Configuration

### Environment Variables (`.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `DEVICE` | cuda/cpu | cuda |
| `STT_MODEL` | Whisper model size | large-v2 |
| `TTS_VOICE` | Piper voice model | en_US-amy-medium |
| `OLLAMA_MODEL` | LLM model | mistral:7b-instruct |
| `FULL_AUTONOMY` | Enable auto-actions | true |
| `SELF_HEAL_ENABLED` | Enable self-repair | true |

---

## 🔌 Extension Points

### Adding New Voice Commands

1. Edit `brain/intent_parser.py`
2. Add pattern matching for new command
3. Implement handler in appropriate module

### Adding New Automation Actions

1. Create action in `automation/`
2. Register in action dispatcher
3. Add voice command mapping

### Adding New Avatar Emotions

1. Add emotion assets to `avatar/models/`
2. Register in `emotion_engine.py`
3. Map trigger conditions

---

## 📊 Performance Characteristics

| Component | Latency | Memory | GPU Usage |
|-----------|---------|--------|-----------|
| ASR (GPU) | 0.5-2s | 2GB VRAM | 50% |
| ASR (CPU) | 3-8s | 2GB RAM | 0% |
| TTS | 0.2s | 500MB RAM | 0% |
| LLM (7B) | 2-5s | 4GB VRAM | 80% |
| Avatar | 16ms | 200MB RAM | 10% |
