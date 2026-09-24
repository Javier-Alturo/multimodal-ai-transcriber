"""Grabacion continua sin cortes — HyperX SoloCast 2."""

import queue
import threading
import time
import wave

import numpy as np
import sounddevice as sd

try:
    import keyboard

    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False

STT_SAMPLE_RATE = 16000


def audio_level(audio):
    if audio is None or len(audio) == 0:
        return 0.0
    return float(np.sqrt(np.mean(audio.astype(np.float64) ** 2)))


def resample_to_16k(audio, source_rate):
    """Convierte a 16 kHz para reconocimiento de voz."""
    if len(audio) == 0:
        return np.array([], dtype=np.float32)
    if source_rate == STT_SAMPLE_RATE:
        return audio.astype(np.float32)

    try:
        from scipy.signal import resample_poly
        # Ej: 44100 -> 16000  =>  up=160, down=441
        return resample_poly(audio, STT_SAMPLE_RATE, source_rate).astype(np.float32)
    except ImportError:
        target_len = int(len(audio) * STT_SAMPLE_RATE / source_rate)
        if target_len < 1:
            return np.array([], dtype=np.float32)
        x_old = np.arange(len(audio))
        x_new = np.linspace(0, len(audio) - 1, target_len)
        return np.interp(x_new, x_old, audio).astype(np.float32)


def _to_mono(chunk):
    if chunk.ndim == 1:
        return chunk.flatten()
    left = chunk[:, 0]
    right = chunk[:, 1]
    return left if audio_level(left) >= audio_level(right) else right


def _record_continuous(device_index, device_rate, stop_event, max_seconds=60):
    """
    Graba en flujo continuo (sin trozos sueltos que suenan entrecortados).
    Devuelve (audio_16k, audio_nativo).
    """
    info = sd.query_devices(device_index, "input")
    channels = min(2, max(1, int(info["max_input_channels"])))
    blocksize = int(device_rate * 0.05)  # bloques de 50 ms

    audio_queue = queue.Queue()
    blocks = []

    def callback(indata, frames, time_info, status):
        if status:
            print(f"\n[Audio] {status}")
        audio_queue.put(indata.copy())

    stream = sd.InputStream(
        device=device_index,
        channels=channels,
        samplerate=device_rate,
        dtype="float32",
        blocksize=blocksize,
        callback=callback,
    )

    started = time.time()
    print("     ", end="", flush=True)

    try:
        stream.start()
        while not stop_event.is_set():
            if time.time() - started > max_seconds:
                print("\n[Tu] Tiempo maximo alcanzado.")
                break
            try:
                data = audio_queue.get(timeout=0.08)
            except queue.Empty:
                continue

            mono = _to_mono(data)
            blocks.append(mono)

            level = audio_level(mono)
            bars = int(min(level * 120, 25))
            print(f"\r     {'#' * bars}{' ' * (25 - bars)} {level:.3f}", end="", flush=True)
    finally:
        stream.stop()
        stream.close()

    print()
    if not blocks:
        empty = np.array([], dtype=np.float32)
        return empty, empty

    native = np.concatenate(blocks)
    stt_audio = resample_to_16k(native, device_rate)
    return stt_audio, native


def _wait_key(key):
    keys_to_try = [key]
    if key == "|":
        keys_to_try = ["|", "shift+\\", "\\", "ç"]

    while True:
        event = keyboard.read_event(suppress=False)
        if event.event_type != keyboard.KEY_DOWN:
            continue
        if event.name in keys_to_try:
            time.sleep(0.15)
            return


def record_toggle_key(device_index, device_rate=44100, max_seconds=60, toggle_key="|"):
    """
    Pulsa tecla -> graba continuo -> misma tecla -> devuelve (audio_16k, audio_nativo, rate).
    """
    if not HAS_KEYBOARD:
        raise RuntimeError("Instala keyboard: py -m pip install keyboard")

    print(f"\n[Tu] Pulsa '{toggle_key}' para EMPEZAR a grabar...")
    _wait_key(toggle_key)

    stop = threading.Event()

    def wait_stop():
        _wait_key(toggle_key)
        stop.set()

    print(f"[Tu] >>> GRABANDO... Pulsa '{toggle_key}' otra vez para ENVIAR")
    threading.Thread(target=wait_stop, daemon=True).start()

    audio_16k, audio_native = _record_continuous(
        device_index, device_rate, stop, max_seconds=max_seconds
    )
    stop.set()
    time.sleep(0.05)
    return audio_16k, audio_native, device_rate


def save_debug_wav(audio, path, sample_rate=STT_SAMPLE_RATE):
    if len(audio) == 0:
        return
    pcm = (np.clip(audio, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())


def test_microphone(device_index, device_rate=44100, seconds=3):
    info = sd.query_devices(device_index, "input")
    channels = min(2, max(1, int(info["max_input_channels"])))
    print(f"[Mic] Prueba {seconds}s @ {device_rate} Hz — HABLA FUERTE...")

    stop = threading.Event()

    def stop_after():
        time.sleep(seconds)
        stop.set()

    threading.Thread(target=stop_after, daemon=True).start()
    _, native = _record_continuous(device_index, device_rate, stop, max_seconds=seconds + 1)

    level = audio_level(native)
    print(f"[Mic] Nivel: {level:.4f}")
    if level < 0.01:
        print("[Mic] MUY BAJO. Sube volumen del SoloCast en Windows > Sonido > Entrada.")
        return False
    return True
