#pragma once
#include <stdint.h>

void writeWavHeader(uint8_t* buffer, size_t dataSize, uint32_t sampleRate, uint16_t bitsPerSample, uint16_t channels) {
  uint32_t chunkSize = 36 + dataSize;
  uint32_t byteRate = sampleRate * channels * bitsPerSample / 8;
  uint16_t blockAlign = channels * bitsPerSample / 8;

  memcpy(buffer, "RIFF", 4);
  memcpy(buffer + 4, &chunkSize, 4);
  memcpy(buffer + 8, "WAVE", 4);
  memcpy(buffer + 12, "fmt ", 4);

  uint32_t subChunk1Size = 16;
  uint16_t audioFormat = 1;

  memcpy(buffer + 16, &subChunk1Size, 4);
  memcpy(buffer + 20, &audioFormat, 2);
  memcpy(buffer + 22, &channels, 2);
  memcpy(buffer + 24, &sampleRate, 4);
  memcpy(buffer + 28, &byteRate, 4);
  memcpy(buffer + 32, &blockAlign, 2);
  memcpy(buffer + 34, &bitsPerSample, 2);

  memcpy(buffer + 36, "data", 4);
  memcpy(buffer + 40, &dataSize, 4);
}

