import time

import pyttsx3
import sounddevice as sd


class LocalTTS:
    def __init__(self, language="es"):
        self.rate = 165
        self.voice_id = None
        probe = pyttsx3.init()
        try:
            self.voice_id = self._pick_voice_id(probe, language)
        finally:
            try:
                probe.stop()
            except Exception:
                pass

    def _pick_voice_id(self, engine, language):
        lang = language.lower()
        keywords = (
            ["spanish", "espanol", "espa", "sabina", "helena", "raul", "laura"]
            if lang.startswith("es")
            else ["english", "zira", "david"]
        )
        for voice in engine.getProperty("voices"):
            name = (voice.name or "").lower()
            if any(k in name for k in keywords):
                print(f"[TTS] Voz: {voice.name}")
                return voice.id
        print("[TTS] Voz por defecto del sistema")
        return None

    def speak(self, text):
        if not text.strip():
            return

        # Libera el microfono antes de hablar (evita conflicto con sounddevice)
        sd.stop()
        time.sleep(0.12)

        engine = pyttsx3.init()
        try:
            engine.setProperty("rate", self.rate)
            if self.voice_id:
                engine.setProperty("voice", self.voice_id)
            engine.say(text)
            engine.runAndWait()
        finally:
            try:
                engine.stop()
            except Exception:
                pass

        time.sleep(0.08)
