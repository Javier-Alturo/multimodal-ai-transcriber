"""Diagnostico del HyperX SoloCast 2."""

import sounddevice as sd

from audio_devices import MIC_DEVICE_INDEX, find_input_device, list_solocast_devices

print("=== HyperX SoloCast 2 en tu PC ===\n")
for i, d in list_solocast_devices():
    mark = " <-- USANDO ESTE" if i == MIC_DEVICE_INDEX else ""
    default = " (default Windows)" if i == sd.default.device[0] else ""
    print(f"  [{i}] {d['name']}{mark}{default}")
    print(f"       {d['max_input_channels']} canales @ {int(d['default_samplerate'])} Hz")

idx, name, rate = find_input_device()
print(f"\nLa app usara: [{idx}] {name} @ {rate} Hz")
print("\nSi no es el correcto, cambia MIC_DEVICE_INDEX en audio_devices.py")
