#pragma once
#include <stddef.h>
#include <stdint.h>

#define MAGIC_WORD 0xB0A1E1A1

#pragma pack(push, 1)
typedef struct {
  uint32_t magic;
  uint16_t version;
  uint16_t model_id;
  uint32_t seq;
  uint32_t t_ms;
  uint16_t intent_id;
  uint16_t conf_q15;
  int16_t aux[18];
  uint64_t mac;
} pkt_t;
#pragma pack(pop)

typedef struct {
  uint8_t act;
  int16_t v0;
} action_t;

uint64_t siphash24(const uint8_t *in, size_t inlen, const uint64_t k[2]);
void chacha20_encrypt(uint8_t *data, size_t len, const uint32_t key[8],
                      uint64_t nonce, uint32_t counter);
