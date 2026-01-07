# Nina's Beats (Symphony Edition)

> A terminal-based audio-visual love experience — a digital love letter for Nina.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Overview

Nina's Beats is an emotionally-driven terminal experience that combines synchronized audio, dynamic visuals, and personalized lyrics into an immersive audio-visual journey. Built with Spec-Driven Development (SDD) methodology and optimized for mobile Termux environments.

**Target:** Termux on Android (40-80 column terminals)
**Philosophy:** Emotional impact over technical utility

## Features

| Feature | Description |
|---------|-------------|
| **7 Visual Scenes** | Intro, Starfield, Matrix Rain, Fireworks, Heartbeat, Waveform, Finale |
| **Audio-Visual Sync** | Lyrics appear within 100ms of vocal timing |
| **Beat-Reactive Visuals** | Particle system responds to music intensity |
| **Zero-Friction Launch** | One command to experience — no configuration |
| **Graceful Degradation** | Never crashes; always shows sweet messages |
| **Battery Efficient** | Targets 24-30 FPS to preserve mobile battery |

## Quick Start

```bash
# Install dependencies
pip install rich

# Run the experience
python -m ninas_beats
```

## Prerequisites

| Requirement | Version/Command |
|-------------|-----------------|
| Python | `3.10+` |
| mpv (audio) | See installation below |

### Installing mpv

**Termux (Android):**
```bash
pkg install mpv
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt install mpv
```

**macOS:**
```bash
brew install mpv
```

## Setup

1. Place your audio file at `assets/audio.mp3`
2. Create `assets/lyrics.json` with timestamps:

```json
{
  "song_title": "Your Song Name",
  "song_artist": "Artist Name",
  "duration_seconds": 180.5,
  "lyrics": [
    {"time": 0.0, "text": "", "scene": "intro"},
    {"time": 10.5, "text": "Wake up, Nina...", "scene": "starfield"},
    {"time": 30.0, "text": "Your lyric here", "scene": "fireworks"}
  ],
  "finale_message": "Forever yours,\nAhsan ♥"
}
```

**Available scenes:** `intro`, `starfield`, `matrix_rain`, `fireworks`, `heartbeat`, `waveform`, `finale`

## Controls

| Key | Action |
|-----|--------|
| `p` | Pause / Resume |
| `q` | Quit to closing message |
| `Enter` | Exit after closing message |

## Project Structure

```
ninas-beats/
├── src/ninas_beats/
│   ├── main.py          # Entry point
│   ├── director.py      # Scene orchestrator
│   ├── audio_manager.py # mpv playback control
│   ├── lyric_sync.py    # Time-based lyric lookup
│   └── scenes/          # Visual scene implementations
├── assets/              # Audio and lyrics
├── tests/               # Test suite
└── pyproject.toml       # Project configuration
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `mpv not found` | Install mpv (see Prerequisites) |
| `Audio file not found` | Ensure `assets/audio.mp3` exists |
| Laggy animation | Close other apps; app auto-reduces particles |

## Development

```bash
# Install in editable mode
pip install -e .

# Run tests
pytest

# Generate lyrics from audio (uses Whisper)
python generate_lyrics.py audio.mp3
```

## License

MIT License — see [LICENSE](LICENSE) for details.

---

**Made with ♥ by Ahsan, for Nina.**

*Every pixel, every delay, every color is for you.*
