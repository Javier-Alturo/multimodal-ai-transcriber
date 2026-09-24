# Multimodal AI Transcriber 🎙️👋

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python)
![MediaPipe](https://img.shields.io/badge/MediaPipe-Hand%20Landmarker-orange?style=flat-square)
![SpeechRecognition](https://img.shields.io/badge/Speech-Google%20API-green?style=flat-square&logo=google)
![OpenCV](https://img.shields.io/badge/OpenCV-Camera%20Vision-red?style=flat-square&logo=opencv)
![License](https://img.shields.io/badge/license-MIT-purple?style=flat-square)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=flat-square)

**Multimodal AI Transcriber** es una aplicación de escritorio que combina **reconocimiento de voz en tiempo real** con **visión por computadora** para crear una experiencia de transcripción controlada por gestos. El sistema escucha tu micrófono continuamente mientras tu cámara detecta un gesto de mano específico — al mostrar una **palma abierta**, la aplicación se detiene automáticamente y guarda tanto la transcripción como el audio y el video de la sesión.

---

## ✨ Características Principales

- **Modo Aprendizaje de Inglés (`--learning`)**: Habla en español, la aplicación lo traduce al inglés y un asistente de voz lo pronuncia para que puedas practicar tu pronunciación (actuando como tu profesor personal).
- **Auto-Detección de Micrófono SoloCast**: Prioriza y se conecta automáticamente al micrófono HyperX SoloCast si está disponible.
- **Transcripción Continua en Tiempo Real**: Escucha tu micrófono en un hilo paralelo usando `SpeechRecognition` + Google Speech API, sin interrumpir la detección de gestos.
- **Control por Gestos (Palma Abierta)**: Usa MediaPipe Hand Landmarker para detectar cuando los 4 dedos principales están extendidos — ningún botón necesario para detener la grabación.
- **Sesiones con Timestamp**: Cada ejecución crea una carpeta nueva en `recordings/<YYYY-MM-DD_HH-MM-SS>/` con 3 archivos: `transcription.txt`, `audio.wav` y `video.mp4`.
- **Calibración de Ruido Ambiental**: El módulo de transcripción ajusta automáticamente el umbral de energía al entorno antes de empezar a escuchar.
- **Guardado Seguro de Audio**: Todos los fragmentos de audio capturados se ensamblan en un único archivo WAV al finalizar la sesión.
- **Grabación de Video Limpia**: La cámara graba el video sin overlays ni anotaciones para que el archivo final sea limpio.
- **Auto-descarga del Modelo AI**: Si el modelo de MediaPipe no está presente, se descarga automáticamente desde Google Storage en el primer uso.

---

## 🏗️ ¿Cómo Funciona?

El sistema tiene dos módulos que corren en paralelo y se sincronizan a través de señales:

```
Usuario ejecuta: python main.py
        │
        ├── Crea carpeta de sesión → recordings/<timestamp>/
        │
        ├── [HILO DAEMON]  Transcriber.start()
        │       │
        │       ├── Calibra micrófono (1.5s de silencio)
        │       ├── Escucha en bucle (timeout=3s, frase max=15s)
        │       ├── Google Speech API → texto reconocido
        │       └── Escribe texto en transcription.txt
        │
        └── [HILO PRINCIPAL]  GestureRecognizer.run()
                │
                ├── Abre cámara (OpenCV VideoCapture)
                ├── Configura VideoWriter → video.mp4
                ├── Frame a frame → MediaPipe Hand Landmarker
                ├── Detecta landmarks de mano
                ├── is_open_palm() → 4 dedos extendidos?
                │       └── SÍ → detiene cámara → return True
                └── Tecla ESC → salida manual → return False
        │
        ↓
Transcriber.stop()
        ├── Señal de parada al hilo daemon
        ├── Ensambla todos los frames de audio
        └── Guarda audio.wav completo
```

### Lógica de Detección de Palma Abierta

El método `is_open_palm()` compara la posición Y de las puntas de los dedos (landmarks 8, 12, 16, 20) contra sus articulaciones PIP (landmarks 6, 10, 14, 18). Si las 4 puntas están **por encima** de sus PIPs en el eje Y, se considera palma abierta:

```python
# Si tip.y < pip.y → el dedo está extendido (hacia arriba en imagen)
open_fingers = sum(1 for tip, pip in zip(tips, pips)
                   if hand_landmarks[tip].y < hand_landmarks[pip].y)
return open_fingers == 4  # Los 4 dedos principales extendidos
```

---

## 📁 Estructura del Proyecto

```
multimodal-ai-transcriber/
├── main.py                   # Punto de entrada — orquesta transcripción y gestos
├── transcription.py          # Módulo de Speech-to-Text (hilo daemon)
├── gesture_recognition.py    # Módulo de visión con MediaPipe (hilo principal)
├── requirements.txt          # Dependencias del proyecto
├── hand_landmarker.task      # Modelo AI de MediaPipe (auto-descarga si no existe)
├── .gitignore                # Excluye venv, pycache, recordings y modelo binario
└── recordings/               # Sesiones guardadas (generado en ejecución)
    └── 2025-05-14_10-30-00/
        ├── transcription.txt # Texto transcrito de la sesión
        ├── audio.wav         # Audio completo de la sesión
        └── video.mp4         # Video grabado de la cámara
```

---

## ⚙️ Módulos en Detalle

### 🎤 `transcription.py` — Transcriber

| Atributo / Método | Descripción |
|---|---|
| `__init__(output_file, audio_file)` | Inicializa recognizer, micrófono y crea el archivo de transcripción |
| `start()` | Lanza el hilo daemon de escucha en background |
| `_listen_loop()` | Bucle principal: calibra, escucha, reconoce y escribe |
| `stop()` | Señal de parada, espera al hilo y guarda el WAV final |
| `energy_threshold = 300` | Umbral de sensibilidad del micrófono (ajustado dinámicamente) |
| `phrase_time_limit = 15s` | Duración máxima de una frase continua |
| `language = "en-US"` | Idioma de reconocimiento de Google Speech API |

### 👋 `gesture_recognition.py` — GestureRecognizer

| Atributo / Método | Descripción |
|---|---|
| `__init__(video_writer_path)` | Descarga el modelo si no existe, inicializa MediaPipe y la cámara |
| `is_open_palm(hand_landmarks)` | Evalúa si los 4 dedos principales están extendidos |
| `run()` | Bucle de frames: detección, dibujado de landmarks y escritura de video |
| `num_hands = 1` | Solo detecta una mano a la vez |
| `min_hand_detection_confidence = 0.5` | Umbral de confianza para detectar una mano |
| `min_tracking_confidence = 0.5` | Umbral de confianza para el tracking frame a frame |

---

## 🚀 Instalación y Uso

### Requisitos Previos

- Python 3.10+
- Cámara web funcional
- Micrófono funcional
- Conexión a internet (para Google Speech API y descarga del modelo la primera vez)

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/Javier-Alturo/Multimodal-AI-Transcriber.git
cd Multimodal-AI-Transcriber

# 2. Crear entorno virtual
python -m venv venv

# En Windows:
venv\Scripts\activate

# En macOS/Linux:
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar la aplicación
python main.py
```

> **Nota:** En el primer uso, la aplicación descarga automáticamente el modelo `hand_landmarker.task` (~7.5 MB) desde Google Storage. Solo ocurre una vez.

### Flujo de Uso

1. Ejecuta `python main.py` (o usa `python main.py --learning` para iniciar el Modo Profesor de Inglés)
2. Permanece **en silencio 1.5 segundos** mientras el micrófono se calibra
3. Empieza a **hablar** — el texto aparecerá en `recordings/<timestamp>/transcription.txt`
4. Muestra una **palma abierta** a la cámara para detener la sesión
5. Los archivos `transcription.txt`, `audio.wav` y `video.mp4` quedan guardados en la carpeta de sesión

---

## 📦 Dependencias

| Librería | Uso |
|---|---|
| `opencv-python` | Captura de cámara, escritura de video y dibujado de landmarks |
| `mediapipe` | Hand Landmarker para detección y tracking de gestos de mano |
| `SpeechRecognition` | Interfaz de micrófono y reconocimiento de voz vía Google API |
| `sounddevice` | Captura de audio, reemplazando pyaudio para mayor compatibilidad |
| `deep-translator` | Traducción automática para el Modo Aprendizaje |
| `pyttsx3` | Text-to-Speech (TTS) para escuchar el guion en inglés |

```bash
pip install -r requirements.txt
```

> **Windows:** Si `pyaudio` falla al instalar, usa el wheel precompilado:
> ```bash
> pip install pipwin
> pipwin install pyaudio
> ```

---

## 🗺️ Roadmap

### ✅ Completado
- Transcripción continua de voz en hilo paralelo
- Control de parada por gesto de palma abierta con MediaPipe
- Grabación y guardado de audio WAV completo
- Grabación de video MP4 sincronizada
- Sesiones con carpetas de timestamp automático
- Auto-descarga del modelo de MediaPipe
- Calibración dinámica de ruido ambiental

### 🔄 En Progreso
- Soporte multiidioma configurable (actualmente `en-US`)
- Overlay de feedback visual en tiempo real (texto reconocido sobre el video)

### 📋 Planeado
- Transcripción offline con **Whisper local** (sin dependencia de Google API)
- Soporte de múltiples gestos (pausa, reinicio, cambio de idioma)
- Interfaz gráfica (GUI) con `tkinter` o `PyQt`
- Exportación a formatos adicionales (SRT, JSON con timestamps)
- Modo solo-audio (sin cámara) con comando de voz para detener
- Dashboard web en tiempo real con WebSockets

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Para cambios mayores, abre un **Issue** primero para discutir lo que deseas cambiar.

```bash
# Flujo recomendado
git checkout -b feat/mi-mejora
git commit -m "feat: descripción de la mejora"
git push origin feat/mi-mejora
# Abre un Pull Request hacia main
```

---

## 📄 Licencia

Este proyecto es Open Source bajo la [Licencia MIT](LICENSE).

---

<div align="center">
  <sub>Hecho con 🎙️ + 👋 por <a href="https://github.com/Javier-Alturo">Javier Alturo</a></sub>
</div>