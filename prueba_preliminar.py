import serial
import mido
import time
import sys

def main():
    print("=== Bridge MIDI ESP32 con loopMIDI ===")
    print("Modo depuración - Mostrando datos crudos")
    
    # Configuración
    SERIAL_PORT = 'COM23'  # Ya sabemos que es COM23
    MIDI_PORT_NAME = 'ESP32_MIDI_Python 1'  # Exactamente como aparece
    BAUD_RATE = 115200
    
    # Conectar al puerto MIDI
    try:
        midi_out = mido.open_output(MIDI_PORT_NAME)
        print(f"✓ Conectado a puerto MIDI: {MIDI_PORT_NAME}")
    except Exception as e:
        print(f"✗ Error conectando a MIDI: {e}")
        input("Presiona Enter para salir...")
        return
    
    # Conectar al Bluetooth
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"✓ Conectado a puerto serial: {SERIAL_PORT}")
    except Exception as e:
        print(f"✗ Error conectando a {SERIAL_PORT}: {e}")
        input("Presiona Enter para salir...")
        return
    
    print("\n🔍 Modo depuración activado")
    print("Mostrando datos crudos del ESP32...")
    print("Presiona Ctrl+C para detener\n")
    
    message_count = 0
    error_count = 0
    
    try:
        while True:
            # Leer todos los bytes disponibles
            available = ser.in_waiting
            if available > 0:
                raw_data = ser.read(available)
                print(f"Bytes recibidos ({available}): {[f'0x{b:02X}' for b in raw_data]}")
                
                # Procesar mensajes MIDI (3 bytes cada uno)
                for i in range(0, len(raw_data), 3):
                    if i + 2 < len(raw_data):
                        status = raw_data[i]
                        control = raw_data[i + 1]
                        value = raw_data[i + 2]
                        
                        print(f"  Mensaje: Status=0x{status:02X}, Control={control}, Value={value}")
                        
                        # Verificar si es mensaje Control Change válido
                        if (status & 0xF0) == 0xB0:  # Es CC message
                            # Filtrar valores fuera de rango MIDI
                            if 0 <= value <= 127 and 0 <= control <= 127:
                                msg = mido.Message('control_change',
                                                 channel=(status & 0x0F),
                                                 control=control,
                                                 value=value)
                                
                                midi_out.send(msg)
                                message_count += 1
                                print(f"✅ MIDI #{message_count}: CC{msg.control} = {msg.value} (Canal {msg.channel+1})")
                            else:
                                error_count += 1
                                print(f"❌ Valor fuera de rango: Control={control}, Value={value}")
                        else:
                            error_count += 1
                            print(f"❌ Mensaje no CC: Status=0x{status:02X}")
            
            time.sleep(0.01)  # Pequeña pausa
            
    except KeyboardInterrupt:
        print(f"\n\n🛑 Deteniendo bridge.")
        print(f"Total mensajes MIDI: {message_count}")
        print(f"Total errores: {error_count}")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
    finally:
        if ser:
            ser.close()
        midi_out.close()
        print("✓ Recursos liberados")
        input("Presiona Enter para salir...")

if __name__ == "__main__":
    main()