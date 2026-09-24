import os
import datetime
import sounddevice as sd
from transcription import Transcriber
from gesture_recognition import GestureRecognizer
import argparse

def get_solocast_device():
    # Intenta buscar el micrófono HyperX SoloCast 2 automáticamente
    devices = sd.query_devices()
    for i, d in enumerate(devices):
        if d['max_input_channels'] > 0 and 'SoloCast' in d['name']:
            return i
    return None # Si no lo encuentra, usa el por defecto

def main():
    parser = argparse.ArgumentParser(description="Multimodal AI Transcriber")
    parser.add_argument('--learning', action='store_true', help='Activar el modo aprendizaje de inglés')
    args = parser.parse_args()

    print("==============================================")
    print(" Welcome to the Speech-to-Text Gesture App!   ")
    print("==============================================")
    
    if args.learning:
        print("🎓 MODO APRENDIZAJE ACTIVADO: Habla en español, y yo lo traduciré y hablaré en inglés.")

    # Buscar el dispositivo de audio correcto
    device_index = get_solocast_device()
    if device_index is not None:
        print(f"🎙️ Micrófono SoloCast detectado en el índice {device_index}")
    else:
        print("⚠️ Micrófono SoloCast no detectado, usando el dispositivo por defecto.")

    # Create timestamped directory
    now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    recordings_dir = os.path.join("recordings", now)
    os.makedirs(recordings_dir, exist_ok=True)
    
    txt_path = os.path.join(recordings_dir, "transcription.txt")
    video_path = os.path.join(recordings_dir, "video.mp4")
    audio_path = os.path.join(recordings_dir, "audio.wav")

    print(f"-> Guardando tus archivos en la carpeta: {recordings_dir}")
    
    transcriber = Transcriber(output_file=txt_path, audio_file=audio_path, device_index=device_index, learning_mode=args.learning)
    # Start the listening thread
    transcriber.start()

    # Create the gesture recognizer and block until gesture detected
    gesture_rec = GestureRecognizer(video_writer_path=video_path)
    stop_detected = gesture_rec.run()

    if stop_detected:
         print("-> Gesture trigger received. Shutting down transcription...")
    else:
         print("-> Manual exit trigger received. Shutting down...")
         
    transcriber.stop()
    print("Application closed securely.")

if __name__ == "__main__":
    main()
