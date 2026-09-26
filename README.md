# Multimodal AI Transcriber 🎙️👋

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python)
![MediaPipe](https://img.shields.io/badge/MediaPipe-Hand%20Landmarker-orange?style=flat-square)
![SpeechRecognition](https://img.shields.io/badge/Speech-Google%20API-green?style=flat-square&logo=google)
![OpenCV](https://img.shields.io/badge/OpenCV-Camera%20Vision-red?style=flat-square&logo=opencv)
![License](https://img.shields.io/badge/license-MIT-purple?style=flat-square)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=flat-square)

**Multimodal AI Transcriber** is a desktop app that combines **real-time speech recognition** with **computer vision** for gesture-controlled transcription. It listens to your microphone the whole time while your camera watches for one hand gesture: when you show an **open palm**, the app stops and saves the transcript, the audio and the video of the session.

---

## ✨ Key Features

- **English learning mode (`--learning`):** speak in Spanish, the app translates it into English and a voice assistant reads it aloud so you can practice your pronunciation.
- **Local English teacher (`teacher.py`):** a speech-to-speech tutor that runs entirely on your machine, with Whisper for speech-to-text, a local LLM through Ollama and local text-to-speech. You talk, it answers and corrects you.
- **Microphone auto-detection:** prefers a configured microphone (a HyperX SoloCast by default, set in `audio_devices.py`) and falls back to any available one.
- **Continuous real-time transcription:** listens in a parallel thread with `SpeechRecognition` + the Google Speech API, without blocking gesture detection.
- **Gesture control (open palm):** MediaPipe Hand Landmarker detects when your 4 main fingers are extended, so you don't need a button to stop recording.
- **Timestamped sessions:** each run creates a new folder `recordings/<YYYY-MM-DD_HH-MM-SS>/` with 3 files: `transcription.txt`, `audio.wav` and `video.mp4`.
- **Background noise calibration:** the transcriber adjusts its energy threshold to the room before it starts listening.
- **Safe audio saving:** every captured audio chunk is joined into a single WAV file at the end of the session.
- **Clean video:** the camera records without overlays, so the final file is clean.
- **Automatic model download:** if the MediaPipe model is missing, it downloads from Google Storage on first use.

---

## 🏗️ How It Works

Two modules run in parallel and stay in sync through signals:

```
User runs: python main.py
        │
        ├── Creates the session folder → recordings/<timestamp>/
        │
        ├── [DAEMON THREAD]  Transcriber.start()
        │       │
        │       ├── Calibrates the microphone (1.5 s of silence)
        │       ├── Listens in a loop (timeout = 3 s, max phrase = 15 s)
        │       ├── Google Speech API → recognized text
        │       └── Writes the text to transcription.txt
        │
        └── [MAIN THREAD]  GestureRecognizer.run()
                │
                ├── Opens the camera (OpenCV VideoCapture)
                ├── Sets up the VideoWriter → video.mp4
                ├── Frame by frame → MediaPipe Hand Landmarker
                ├── Detects the hand landmarks
                ├── is_open_palm() → 4 fingers extended?
                │       └── YES → stops the camera → return True
                └── ESC key → manual exit → return False
        │
        ↓
Transcriber.stop()
        ├── Signals the daemon thread to stop
        ├── Joins all the audio frames
        └── Saves the complete audio.wav
```

### Open-palm detection logic

`is_open_palm()` compares the Y position of the fingertips (landmarks 8, 12, 16, 20) with their PIP joints (landmarks 6, 10, 14, 18). If all 4 tips are **above** their PIP joints on the Y axis, the hand counts as an open palm:

```python
# If tip.y < pip.y → the finger is extended (pointing up in the image)
open_fingers = sum(1 for tip, pip in zip(tips, pips)
                   if hand_landmarks[tip].y < hand_landmarks[pip].y)
return open_fingers == 4  # all 4 main fingers extended
```

---

## 📁 Project Structure

```
multimodal-ai-transcriber/
├── main.py                   # Entry point — runs transcription and gestures together
├── transcription.py          # Speech-to-text module (daemon thread)
├── gesture_recognition.py    # MediaPipe vision module (main thread)
├── video_recorder.py         # Camera recording
├── teacher.py                # Local English teacher (speech-to-speech)
├── english_teacher.py        # Tutor logic and prompts (Ollama)
├── local_stt.py              # Local speech-to-text (Whisper, with Google fallback)
├── local_tts.py              # Local text-to-speech (pyttsx3)
├── push_to_talk.py           # Push-to-talk recording
├── audio_devices.py          # Microphone selection
├── check_mic.py              # Microphone diagnostics
├── list_devices.py           # Lists audio devices
├── requirements.txt          # Dependencies for the transcriber
├── requirements-teacher.txt  # Dependencies for the English teacher
└── recordings/               # Saved sessions (created at runtime)
    └── 2025-05-14_10-30-00/
        ├── transcription.txt # Session transcript
        ├── audio.wav         # Full session audio
        └── video.mp4         # Camera video
```

---

## ⚙️ Modules in Detail

### 🎤 `transcription.py` — Transcriber

| Attribute / Method | Description |
|---|---|
| `__init__(output_file, audio_file)` | Sets up the recognizer and microphone and creates the transcript file |
| `start()` | Starts the background listening thread |
| `_listen_loop()` | Main loop: calibrates, listens, recognizes and writes |
| `stop()` | Signals the thread to stop, waits for it and saves the final WAV |
| `energy_threshold = 300` | Microphone sensitivity (adjusted dynamically) |
| `phrase_time_limit = 15s` | Maximum length of a continuous phrase |
| `language = "en-US"` | Google Speech API recognition language |

### 👋 `gesture_recognition.py` — GestureRecognizer

| Attribute / Method | Description |
|---|---|
| `__init__(video_writer_path)` | Downloads the model if needed and sets up MediaPipe and the camera |
| `is_open_palm(hand_landmarks)` | Checks whether the 4 main fingers are extended |
| `run()` | Frame loop: detection, landmark drawing and video writing |
| `num_hands = 1` | Detects one hand at a time |
| `min_hand_detection_confidence = 0.5` | Confidence threshold to detect a hand |
| `min_tracking_confidence = 0.5` | Confidence threshold for frame-to-frame tracking |

---

## 🚀 Installation and Usage

### Prerequisites

- Python 3.10+
- A working webcam
- A working microphone
- Internet connection (for the Google Speech API and the first model download)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/Javier-Alturo/multimodal-ai-transcriber.git
cd multimodal-ai-transcriber

# 2. Create a virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate

# 3. Install the dependencies
pip install -r requirements.txt

# 4. Run the app
python main.py
```

> **Note:** on first use, the app downloads the `hand_landmarker.task` model (~7.5 MB) from Google Storage. This only happens once.

### How to use it

1. Run `python main.py` (or `python main.py --learning` for English learning mode)
2. Stay **silent for 1.5 seconds** while the microphone calibrates
3. Start **speaking** — the text appears in `recordings/<timestamp>/transcription.txt`
4. Show an **open palm** to the camera to end the session
5. `transcription.txt`, `audio.wav` and `video.mp4` are saved in the session folder

### Local English teacher

```bash
pip install -r requirements-teacher.txt
ollama pull llama3.2
python teacher.py
```

Press `|` to start recording, and `|` again to send what you said. The teacher answers out loud.

---

## 📦 Dependencies

| Library | Used for |
|---|---|
| `opencv-python` | Camera capture, video writing and landmark drawing |
| `mediapipe` | Hand Landmarker for gesture detection and tracking |
| `SpeechRecognition` | Microphone interface and speech recognition through the Google API |
| `sounddevice` | Audio capture (replaces pyaudio for better compatibility) |
| `deep-translator` | Automatic translation for learning mode |
| `pyttsx3` | Text-to-speech, to hear the English sentence |
| `faster-whisper` | Local speech-to-text for the English teacher |
| `ollama` | Local LLM for the English teacher |

> **Windows:** if `pyaudio` fails to install, use the precompiled wheel:
> ```bash
> pip install pipwin
> pipwin install pyaudio
> ```

---

## 🗺️ Roadmap

### ✅ Done
- Continuous speech transcription in a parallel thread
- Open-palm stop gesture with MediaPipe
- Full WAV audio recording and saving
- Synchronized MP4 video recording
- Automatic timestamped session folders
- Automatic MediaPipe model download
- Dynamic background noise calibration
- Local speech-to-speech English teacher (Whisper + Ollama + TTS)

### 🔄 In progress
- Configurable language (currently `en-US`)
- Real-time visual feedback (recognized text over the video)

### 📋 Planned
- Offline transcription with local Whisper in the main recorder too (no Google API)
- More gestures (pause, restart, switch language)
- Desktop GUI with `tkinter` or `PyQt`
- Export to more formats (SRT, JSON with timestamps)
- Audio-only mode (no camera) with a voice command to stop
- Real-time web dashboard with WebSockets

---

## 🤝 Contributing

Contributions are welcome. For bigger changes, open an **issue** first to discuss what you'd like to change.

```bash
# Suggested flow
git checkout -b feat/my-improvement
git commit -m "feat: describe the improvement"
git push origin feat/my-improvement
# Then open a pull request to main
```

---

## 📄 License

Open source under the [MIT License](LICENSE).

---

<div align="center">
  <sub>Made with 🎙️ + 👋 by <a href="https://github.com/Javier-Alturo">Javier Alturo</a></sub>
</div>
