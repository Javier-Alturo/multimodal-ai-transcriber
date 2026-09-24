import os

import numpy as np
import sounddevice as sd

# Intenta arreglar SSL para descargar Whisper en Windows
try:
    import certifi
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
except ImportError:
    pass


class LocalSTT:
    """Speech-to-text: Whisper local si esta disponible, si no Google (requiere internet)."""

    def __init__(self, model_size="base", device_index=None, language="en", use_whisper=None):
        self.device_index = device_index
        self.language = language
        self.sample_rate = 16000
        self.backend = None
        self._google = None

        if use_whisper is None:
            use_whisper = os.environ.get("USE_WHISPER", "0") == "1"

        if not use_whisper:
            self._init_google()
            return

        try:
            from faster_whisper import WhisperModel
            print(f"[STT] Cargando Whisper '{model_size}' (local)...")
            self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
            self.backend = "whisper"
            print("[STT] Whisper listo (100% local).")
        except Exception as e:
            print(f"[STT] Whisper no disponible ({e.__class__.__name__}).")
            self._init_google()

    def _init_google(self):
        print("[STT] Usando Google Speech (necesita internet para escucharte).")
        import speech_recognition as sr
        self._google = sr.Recognizer()
        self._google.energy_threshold = 150
        self._google.dynamic_energy_threshold = False
        self._google.pause_threshold = 0.6
        self.backend = "google"
        google_langs = {"en": "en-US", "es": "es-ES"}
        self._google_lang = google_langs.get(self.language, f"{self.language}-{self.language.upper()}")

    def record(self, seconds, sample_rate=16000):
        frames = int(seconds * sample_rate)
        audio = sd.rec(
            frames,
            samplerate=sample_rate,
            channels=1,
            dtype="float32",
            device=self.device_index,
        )
        sd.wait()
        return audio.flatten()

    def transcribe(self, audio, sample_rate=16000, min_rms=0.003):
        if audio is None or len(audio) == 0:
            return ""
        rms = float(np.sqrt(np.mean(audio.astype(np.float64) ** 2)))
        if rms < min_rms:
            return ""

        # Normaliza audio bajo para que Google lo entienda mejor
        if rms < 0.06:
            gain = min(12.0, 0.08 / rms)
            audio = np.clip(audio * gain, -1.0, 1.0)

        if self.backend == "whisper":
            segments, _ = self.model.transcribe(
                audio,
                language=self.language,
                vad_filter=True,
                beam_size=1,
            )
            return " ".join(seg.text.strip() for seg in segments).strip()

        import speech_recognition as sr
        pcm = (audio * 32767).astype(np.int16).tobytes()
        audio_data = sr.AudioData(pcm, sample_rate, 2)
        try:
            return self._google.recognize_google(audio_data, language=self._google_lang)
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            raise RuntimeError(f"Error de conexion STT: {e}") from e
