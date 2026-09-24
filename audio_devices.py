import sounddevice as sd

MIC_NAME = "SoloCast 2"
# Fuerza este indice si lo conoces (1 = SoloCast en tu PC). None = auto.
MIC_DEVICE_INDEX = 1


def list_solocast_devices():
    """Lista todos los dispositivos SoloCast visibles."""
    found = []
    for i, device in enumerate(sd.query_devices()):
        if device["max_input_channels"] > 0 and "solocast" in device["name"].lower():
            if "ngenuity" not in device["name"].lower() and "virtual" not in device["name"].lower():
                found.append((i, device))
    return found


def find_input_device(name_substring=MIC_NAME, force_index=None):
    if force_index is not None:
        info = sd.query_devices(force_index, "input")
        return force_index, info["name"], int(info["default_samplerate"])

    if MIC_DEVICE_INDEX is not None:
        info = sd.query_devices(MIC_DEVICE_INDEX, "input")
        name = info["name"]
        if name_substring.lower() in name.lower():
            return MIC_DEVICE_INDEX, name, int(info["default_samplerate"])

    matches = list_solocast_devices()
    if not matches:
        raise RuntimeError(
            f"No se encontro '{name_substring}'. Ejecuta: py check_mic.py"
        )

    # Preferir el que Windows tiene como predeterminado
    try:
        default_idx = sd.default.device[0]
        for i, device in matches:
            if i == default_idx:
                return i, device["name"], int(device["default_samplerate"])
    except Exception:
        pass

    i, device = matches[0]
    return i, device["name"], int(device["default_samplerate"])
