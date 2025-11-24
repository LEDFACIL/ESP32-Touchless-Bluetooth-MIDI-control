# test_installation.py
try:
    import mido
    import serial
    import rtmidi
    print("✅ Todos los módulos instalados correctamente!")
    print("Puertos MIDI disponibles:", mido.get_output_names())
except ImportError as e:
    print(f"❌ Error: {e}")
input("Presiona Enter para salir...")