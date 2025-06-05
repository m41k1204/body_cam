#include "config.h"
#include "audio_config.h"
#include "wav_utils.h"
#include <WiFi.h>
#include <HTTPClient.h>

#define AUDIO_DURATION_SEC 60
#define SAMPLE_RATE 16000
#define BITS_PER_SAMPLE 16
#define CHANNELS 1

const size_t audio_data_size = SAMPLE_RATE * (BITS_PER_SAMPLE / 8) * CHANNELS * AUDIO_DURATION_SEC;
uint8_t audio_buffer[audio_data_size + 44]; // 44 bytes for WAV header

void setup() {
  Serial.begin(115200);
  connectToWiFi();
  setupI2S();
}

void loop() {
  Serial.println("Grabando audio...");
  recordAudio(audio_buffer + 44, audio_data_size);
  Serial.println("Audio capturado");

  writeWavHeader(audio_buffer, audio_data_size, SAMPLE_RATE, BITS_PER_SAMPLE, CHANNELS);
  Serial.println("Encabezado WAV agregado");

  Serial.println("Enviando audio a servidor...");
  sendAudioToServer(audio_buffer, audio_data_size + 44);

  delay(60000);  // espera 1 minuto antes de volver a grabar
}

