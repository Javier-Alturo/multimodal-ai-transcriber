import speech_recognition as sr
import threading
import sounddevice as sd
import numpy as np
import io
from deep_translator import GoogleTranslator
import pyttsx3

class Transcriber:
    def __init__(self, output_file="transcription.txt", audio_file="audio.wav", device_index=None, learning_mode=False):
        self.output_file = output_file
        self.audio_file = audio_file
        self.device_index = device_index
        self.learning_mode = learning_mode
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True

        self.stop_listening_signal = False
        self.thread = None

        # Audio saving
        self.audio_frames = []
        self.sample_rate = 16000
        self.sample_width = 2  # 16-bit audio
        
        # Text to Speech Engine for learning mode
        self.tts_engine = None
        if self.learning_mode:
            self.tts_engine = pyttsx3.init()
            voices = self.tts_engine.getProperty('voices')
            # Intentar seleccionar una voz en inglés si está disponible
            for voice in voices:
                if 'english' in voice.name.lower() or 'en-us' in voice.id.lower():
                    self.tts_engine.setProperty('voice', voice.id)
                    break

        # Write header to output
        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write("--- Start of Transcription ---\n")

    def _record_chunk(self, duration=5, samplerate=16000):
        """Graba un bloque de audio con sounddevice y lo devuelve como AudioData."""
        recording = sd.rec(
            int(duration * samplerate),
            samplerate=samplerate,
            channels=1,
            dtype='int16',
            device=self.device_index
        )
        sd.wait()
        raw_bytes = recording.tobytes()
        return sr.AudioData(raw_bytes, samplerate, 2)

    def start(self):
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()

    def _listen_loop(self):
        print("[Transcriber] Calibrando microfono para ruido de fondo... pido silencio por 1 segundo.")

        # Calibración: grabamos 1.5 segundos de silencio para ajustar el umbral
        calibration = sd.rec(int(1.5 * self.sample_rate), samplerate=self.sample_rate, channels=1, dtype='int16', device=self.device_index)
        sd.wait()
        cal_data = calibration.tobytes()
        cal_audio = sr.AudioData(cal_data, self.sample_rate, self.sample_width)
        with sr.AudioFile(io.BytesIO(cal_audio.get_wav_data())) as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1.0)

        print(f"[Transcriber] ¡Microfono listo! (Modo Aprendizaje: {'ACTIVADO' if self.learning_mode else 'DESACTIVADO'})")

        while not self.stop_listening_signal:
            try:
                print("[Transcriber] Escuchando...")
                audio = self._record_chunk(duration=5, samplerate=self.sample_rate)

                # Guarda frames para WAV final
                self.audio_frames.append(audio.frame_data)

                print("[Transcriber] Procesando audio (puedes seguir hablando)...")
                
                # En modo aprendizaje escuchamos español, de lo contrario inglés
                lang = "es-ES" if self.learning_mode else "en-US"
                text = self.recognizer.recognize_google(audio, language=lang)
                
                if self.learning_mode:
                    print(f"\n[Transcriber] 🇪🇸 Reconocido (ES): '{text}'")
                    english_text = GoogleTranslator(source='es', target='en').translate(text)
                    print(f"[Transcriber] 🇬🇧 Traducción (EN): '{english_text}'")
                    print("[Transcriber] 🗣️ Repite el guion...")
                    
                    with open(self.output_file, "a", encoding="utf-8") as f:
                        f.write(f"ES: {text}\nEN: {english_text}\n---\n")
                        
                    # El asistente habla la traducción en inglés para que la escuches
                    self.tts_engine.say(english_text)
                    self.tts_engine.runAndWait()
                    
                else:
                    print(f"[Transcriber] Reconocido: '{text}'")
                    with open(self.output_file, "a", encoding="utf-8") as f:
                        f.write(text + "\n")

            except sr.UnknownValueError:
                print("[Transcriber] No se entendió el audio. Intenta hablar más claro.")
            except sr.RequestError as e:
                print(f"[Transcriber] Error de conexión a internet: {e}")
            except Exception as e:
                if not self.stop_listening_signal:
                    print(f"[Transcriber] Error: {e}")

    def stop(self):
        print("[Transcriber] Deteniendo la transcripción de forma segura... Por favor espera.")
        self.stop_listening_signal = True
        if self.thread is not None:
            self.thread.join(timeout=5)

        # Guarda todo el audio capturado en un solo WAV
        if self.audio_frames and self.sample_rate:
            print(f"[Transcriber] Guardando archivo de audio en: {self.audio_file}...")
            full_audio = b"".join(self.audio_frames)
            final_audio = sr.AudioData(full_audio, self.sample_rate, self.sample_width)
            with open(self.audio_file, "wb") as f:
                f.write(final_audio.get_wav_data())

        print("[Transcriber] Detenido completamente.")
