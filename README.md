# 🤖 Jerry — AI Voice Assistant

Jerry is a smart, voice-activated personal AI assistant built in Python. It listens to your voice, understands what you need, and responds instantly — either with plain text answers or by analyzing your screen if needed. Jerry is designed to feel like a real assistant: fast, sharp, and no fluff.

---

## ✨ Features

- 🎙️ **Voice Activation** — Hold `ALT + K` to speak. Jerry listens and transcribes your voice using **OpenAI Whisper**.
- 🧠 **AI-Powered Brain** — Uses **Groq API** with `LLaMA 3.3 70B` for lightning-fast, intelligent text responses.
- 👁️ **Screen Vision** — Say "look at my screen" or "fix this error" and Jerry automatically captures your screen and sends it to **LLaMA 4 Scout Vision** for analysis.
- 🗣️ **Natural Voice Output** — Responds out loud using **Microsoft Edge TTS** (`en-US-JennyNeural` voice) for smooth, human-like speech.
- 💾 **User Memory** — Learns and remembers personal facts and preferences across sessions, stored in `user_profile.txt`.
- 🖥️ **Minimal UI** — A clean overlay window displays both your query and Jerry's response in real time.
- 🔁 **Streaming Responses** — Answers stream in token-by-token for a fast, live feel.
- 🧵 **Threaded Architecture** — Memory learning, speech, and UI updates run in parallel for zero lag.

---

## 🗂️ Project Structure

| File | Role |
|------|------|
| `main.py` | Entry point — validates API, starts the assistant |
| `ears.py` | Listens for `ALT+K`, records and transcribes speech via Whisper |
| `brain.py` | Routes queries to Groq text or vision, manages memory & history |
| `mouth.py` | Converts AI responses to speech using Edge TTS |
| `eyes.py` | Captures screen snapshots for vision queries |
| `ui.py` | Overlay GUI showing conversation |
| `config.py` | API keys, model names, and settings |

---

## ⚙️ Setup

```bash
pip install groq openai-whisper edge-tts pyautogui keyboard pillow sounddevice
```

1. Add your **Groq API key** to `config.py`
2. Run: `python main.py`
3. Hold **ALT + K** to talk to Jerry

---

## 🔑 Requirements

- Python 3.10+
- [Groq API Key](https://console.groq.com)
- Windows OS (for keyboard hooks & Edge TTS)

---

> Built with ❤️ using Groq, Whisper, and Microsoft Edge TTS.
