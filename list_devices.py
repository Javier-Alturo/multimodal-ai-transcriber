import sounddevice as sd

print("\n=== DISPOSITIVOS DE AUDIO DISPONIBLES ===\n")
devices = sd.query_devices()
for i, d in enumerate(devices):
    if d['max_input_channels'] > 0:
        default_marker = " <-- DEFECTO" if i == sd.default.device[0] else ""
        print(f"[{i}] {d['name']} | canales: {d['max_input_channels']}{default_marker}")

print(f"\nDispositivo de entrada por defecto: {sd.default.device[0]}")
print(f"Detalles: {sd.query_devices(sd.default.device[0])['name']}")
