#include "BluetoothSerial.h"

BluetoothSerial SerialBT;

// Pines de los sensores ultrasónicos
#define TRIG1 4
#define ECHO1 5
#define TRIG2 18
#define ECHO2 19

// Buffers para promediar
const int BUFFER_SIZE = 8;  // Número de lecturas para promediar
int buffer1[BUFFER_SIZE] = {0};
int buffer2[BUFFER_SIZE] = {0};
int bufferIndex = 0;

// Últimos valores enviados
int lastValue1 = -1;
int lastValue2 = -1;

// --------------------------------------------------------
// Función genérica para medir distancia de un sensor ultr.
// --------------------------------------------------------
long leerDistanciaMM(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duracion = pulseIn(echoPin, HIGH, 30000);
  if (duracion == 0) return -1;

  long distancia = (duracion * 0.343) / 2;
  return distancia;
}

// --------------------------------------------------------
// Función para promediar lecturas
// --------------------------------------------------------
int promedioLectura(int* buffer, long nuevaLectura) {
  // Agregar nueva lectura al buffer
  buffer[bufferIndex] = nuevaLectura;
  
  // Calcular promedio
  long suma = 0;
  int lecturasValidas = 0;
    for(int i = 0; i < BUFFER_SIZE; i++) {
    if(buffer[i] > 0 && buffer[i] < 1000) { // Filtrar valores extremos
      suma += buffer[i];
      lecturasValidas++;
    }
  }
  
  return (lecturasValidas > 0) ? (suma / lecturasValidas) : nuevaLectura;
}

// --------------------------------------------------------
// Función para mapear y limitar valores MIDI
// --------------------------------------------------------
int mapToMidi(long distancia) {
  if (distancia <= 0) return 0;
  if (distancia < 50) return 0;
  if (distancia > 350) return 127;
  
  return map(distancia, 50, 350, 0, 127);
}

// --------------------------------------------------------
// Función para enviar mensajes MIDI
// --------------------------------------------------------
void sendControlChange(byte control, byte value, byte channel) {
  value = constrain(value, 0, 127);
  control = constrain(control, 0, 127);
  channel = constrain(channel, 1, 16);
  
  byte status = 0xB0 | ((channel - 1) & 0x0F);
  SerialBT.write(status);
  SerialBT.write(control);
  SerialBT.write(value);
}

void setup() {
  Serial.begin(115200);
  SerialBT.begin("ESP32_MIDI_BT");

  pinMode(TRIG1, OUTPUT);
  pinMode(ECHO1, INPUT);
  pinMode(TRIG2, OUTPUT);
  pinMode(ECHO2, INPUT);

  // Inicializar buffers
  for(int i = 0; i < BUFFER_SIZE; i++) {
    buffer1[i] = 200; // Valor inicial razonable
    buffer2[i] = 200;
  }

  Serial.println("ESP32 listo con filtro promediador");
}

void loop() {
  long distancia1 = leerDistanciaMM(TRIG1, ECHO1);
  long distancia2 = leerDistanciaMM(TRIG2, ECHO2);

  // Aplicar filtro promediador
  int distanciaFiltrada1 = promedioLectura(buffer1, distancia1);
  int distanciaFiltrada2 = promedioLectura(buffer2, distancia2);

  // Mapear a MIDI
  int midiValue1 = mapToMidi(distanciaFiltrada1);
  int midiValue2 = mapToMidi(distanciaFiltrada2);

  // Incrementar índice del buffer (circular)
  bufferIndex = (bufferIndex + 1) % BUFFER_SIZE;

  // Enviar solo si hay cambio significativo (reducir salidas)
  if (abs(midiValue1 - lastValue1) >= 1) {  // Más sensible pero menos mensajes
    sendControlChange(10, midiValue1, 1);
    lastValue1 = midiValue1;
    Serial.print("S1: ");
    Serial.print(distanciaFiltrada1);
    Serial.print("mm -> MIDI: ");
    Serial.println(midiValue1);
  }

  if (abs(midiValue2 - lastValue2) >= 1) {
    sendControlChange(11, midiValue2, 1);
    lastValue2 = midiValue2;
    Serial.print("S2: ");
    Serial.print(distanciaFiltrada2);
    Serial.print("mm -> MIDI: ");
    Serial.println(midiValue2);
  }

  delay(40); // Lectura más lenta pero más estable
}