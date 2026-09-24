"""
Profesor local speech-to-speech.

Uso: py teacher.py

Control: pulsa | para grabar, | otra vez para enviar.
"""

import datetime
import os
import sys

from ollama import Client

from audio_devices import find_input_device
from english_teacher import EnglishTeacher, is_quit
from local_stt import LocalSTT
from local_tts import LocalTTS
from push_to_talk import audio_level, record_toggle_key, save_debug_wav, test_microphone

# --- Configuracion ---
LANGUAGE = "es"
PTT_KEY = "|"
WHISPER_MODEL = "base"
OLLAMA_MODEL = "llama3.2:latest"
MAX_RECORD_SECONDS = 60
MIC_NAME = "SoloCast 2"
USE_WHISPER = False
MIN_AUDIO_LEVEL = 0.008

OLLAMA_HOST = "http://127.0.0.1:11434"

GREETINGS = {
    "es": "Hola! Pulsa la tecla |, habla, y vuelve a pulsar | para que te escuche.",
    "en": "Hello! Press |, speak, then press | again so I can hear you.",
}
GOODBYES = {
    "es": "Hasta luego! Sigue practicando.",
    "en": "Goodbye! Keep practicing.",
}


def ensure_ollama_running():
    try:
        Client(host=OLLAMA_HOST).list()
        return True
    except (ConnectionError, OSError):
        print("ERROR: Ollama no esta en ejecucion. Abre la app Ollama.")
        return False


def main():
    lang_label = "Espanol" if LANGUAGE == "es" else "Ingles"

    print("==============================================")
    print(f"   Profesor de {lang_label} (IA local)          ")
    print("==============================================")
    print(f"-> Tecla:  '{PTT_KEY}'  = empezar / terminar de hablar")
    print(f"-> IA:     Ollama ({OLLAMA_MODEL})")
    print(f"-> Voz:    Sistema Windows (offline)")
    print("-> Di 'salir' en un mensaje o Ctrl+C para cerrar.\n")

    if not ensure_ollama_running():
        sys.exit(1)

    try:
        import keyboard  # noqa: F401
    except ImportError:
        print("ERROR: falta el paquete keyboard. Ejecuta: py -m pip install keyboard")
        sys.exit(1)

    mic_index, mic_name, mic_rate = find_input_device(MIC_NAME)
    print(f"-> Microfono FIJO: [{mic_index}] {mic_name}")
    print(f"-> Frecuencia nativa: {mic_rate} Hz (mejor calidad para SoloCast)\n")

    if not test_microphone(mic_index, mic_rate):
        print("-> Arregla el volumen del micro y vuelve a ejecutar.\n")

    stt_lang = "es" if LANGUAGE == "es" else "en"
    stt = LocalSTT(
        model_size=WHISPER_MODEL,
        device_index=mic_index,
        language=stt_lang,
        use_whisper=USE_WHISPER,
    )
    teacher = EnglishTeacher(model=OLLAMA_MODEL, language=LANGUAGE)
    tts = LocalTTS(language=LANGUAGE)

    session_dir = os.path.join(
        "recordings",
        f"teacher_{LANGUAGE}_" + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
    )
    os.makedirs(session_dir, exist_ok=True)
    audios_dir = os.path.join(session_dir, "audios")
    os.makedirs(audios_dir, exist_ok=True)
    log_path = os.path.join(session_dir, "session.txt")

    with open(log_path, "w", encoding="utf-8") as log:
        log.write(f"--- Sesion profesor ({lang_label}) ---\n\n")

    print(f"[Profesor] {GREETINGS.get(LANGUAGE, GREETINGS['es'])}\n")
    print(f"-> Cada grabacion con | se guarda en: {audios_dir}\n")

    turn = 0
    try:
        while True:
            turn += 1
            print(f"--- Turno {turn} ---")

            audio_stt, audio_nativo, native_rate = record_toggle_key(
                mic_index,
                mic_rate,
                MAX_RECORD_SECONDS,
                toggle_key=PTT_KEY,
            )

            level = audio_level(audio_nativo)
            duration = len(audio_nativo) / native_rate if len(audio_nativo) else 0
            wav_name = f"turno_{turn:03d}.wav"
            wav_path = os.path.join(audios_dir, wav_name)
            # WAV a calidad nativa (44100) — suena claro al reproducir
            save_debug_wav(audio_nativo, wav_path, sample_rate=native_rate)
            print(f"[Tu] Grabado: {duration:.1f}s, nivel {level:.3f}")
            print(f"[Tu] Audio guardado ({native_rate} Hz): {wav_path}")

            if level < MIN_AUDIO_LEVEL:
                print("[Tu] Casi sin sonido. Sube volumen del micro o habla mas fuerte.\n")
                continue

            if duration < 0.4:
                print("[Tu] Muy corto. Manten | pulsado un poco mas mientras hablas.\n")
                continue

            print("[Tu] Procesando...")
            user_text = stt.transcribe(audio_stt, min_rms=0.001)

            if not user_text:
                print("[Tu] No se entendio. Habla mas claro o un poco mas largo.\n")
                continue

            print(f"[Tu] {user_text}")

            if is_quit(user_text):
                print(f"\n[Profesor] {GOODBYES.get(LANGUAGE, GOODBYES['es'])}")
                break

            print("[Profesor] Pensando...")
            correction, reply = teacher.respond(user_text)

            if correction:
                print(f"[Correccion] {correction}")
            print(f"[Profesor] {reply}\n")

            with open(log_path, "a", encoding="utf-8") as log:
                log.write(f"Tu: {user_text}\n")
                if correction:
                    log.write(f"Correccion: {correction}\n")
                log.write(f"Profesor: {reply}\n\n")

            print("[Profesor] Hablando...")
            tts.speak(reply)

    except KeyboardInterrupt:
        print("\n\n[Profesor] Sesion terminada.")

    print(f"\n-> Texto: {log_path}")
    print(f"-> Audios: {audios_dir}")


if __name__ == "__main__":
    main()
