import serial
import mido
import time
import sys
from datetime import datetime

def connect_serial(port, baud_rate):
    """Intenta conectar al puerto serial con manejo de errores"""
    try:
        ser = serial.Serial(port, baud_rate, timeout=1)
        print(f"✅ Conectado a {port}")
        return ser
    except serial.SerialException as e:
        print(f"❌ Error conectando a {port}: {e}")
        return None

def connect_midi(port_name):
    """Intenta conectar al puerto MIDI"""
    try:
        midi_out = mido.open_output(port_name)
        print(f"✅ Conectado a MIDI: {port_name}")
        return midi_out
    except Exception as e:
        print(f"❌ Error conectando a MIDI: {e}")
        return None

def main():
    print("=== Bridge MIDI ESP32 - Reconexión Automática ===")
    print("Presiona Ctrl+C para salir\n")
    
    # Configuración
    SERIAL_PORT = 'COM23'
    MIDI_PORT_NAME = 'ESP32_MIDI_Python 1'
    BAUD_RATE = 115200
    
    # Variables de estado
    ser = None
    midi_out = None
    last_message_time = time.time()
    connection_attempts = 0
    max_attempts = 5
    message_count = 0
    
    # Bucle principal con reconexión
    while True:
        try:
            # Verificar/conectar MIDI
            if midi_out is None:
                print("🔌 Conectando a puerto MIDI...")
                midi_out = connect_midi(MIDI_PORT_NAME)
                if midi_out is None:
                    print("🕒 Reintentando MIDI en 3 segundos...")
                    time.sleep(3)
                    continue
            
            # Verificar/conectar Serial
            if ser is None:
                print("🔌 Conectando a ESP32...")
                ser = connect_serial(SERIAL_PORT, BAUD_RATE)
                if ser is None:
                    connection_attempts += 1
                    if connection_attempts >= max_attempts:
                        print("🔄 Reiniciando búsqueda de puertos...")
                        connection_attempts = 0
                    print(f"🕒 Reintentando ESP32 en 5 segundos... (Intento {connection_attempts})")
                    time.sleep(5)
                    continue
                else:
                    connection_attempts = 0
                    last_message_time = time.time()  # Reset timer
                    print("🎹 Bridge MIDI ACTIVO! Mueve tus manos para probar.")
            
            # Verificar timeout (si no hay datos por mucho tiempo)
            current_time = time.time()
            if current_time - last_message_time > 10:  # 10 segundos sin datos
                print("⏰ Timeout: No hay datos del ESP32. Verificando conexión...")
                if ser:
                    ser.close()
                    ser = None
                continue
            
            # Leer datos si disponibles
            if ser.in_waiting >= 3:
                status = ser.read()[0]
                control = ser.read()[0]
                value = ser.read()[0]
                
                # Verificar que es Control Change y valores válidos
                if (status & 0xF0) == 0xB0 and 0 <= value <= 127:
                    msg = mido.Message('control_change',
                                     channel=(status & 0x0F),
                                     control=control,
                                     value=value)
                    
                    midi_out.send(msg)
                    message_count += 1
                    last_message_time = current_time
                    
                    # Mostrar mensaje cada 10 para no saturar consola
                    if message_count % 10 == 0:
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"[{timestamp}] 🎛️ CC{control} = {value} (Total: {message_count})")
            
            # Pequeña pausa para no saturar CPU
            time.sleep(0.001)
            
        except serial.SerialException as e:
            print(f"🔌 Error de conexión serial: {e}")
            print("🔄 Intentando reconexión...")
            if ser:
                ser.close()
                ser = None
            time.sleep(2)
            
        except KeyboardInterrupt:
            print("\n🛑 Deteniendo bridge...")
            break
            
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            print("🔄 Reintentando en 3 segundos...")
            time.sleep(3)
    
    # Limpieza al salir
    print("\n🧹 Cerrando conexiones...")
    if ser:
        ser.close()
    if midi_out:
        midi_out.close()
    print(f"✅ Bridge detenido. Total mensajes enviados: {message_count}")
    print("¡Hasta la próxima! 🎵")

if __name__ == "__main__":
    main()