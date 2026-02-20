#include "protocol.h"
#include <string.h>

#define ROTL32(v, n) (((v) << (n)) | ((v) >> (32 - (n))))
#define QUARTERROUND(x, a, b, c, d)                                            \
  x[a] += x[b];                                                                \
  x[d] = ROTL32(x[d] ^ x[a], 16);                                              \
  x[c] += x[d];                                                                \
  x[b] = ROTL32(x[b] ^ x[c], 12);                                              \
  x[a] += x[b];                                                                \
  x[d] = ROTL32(x[d] ^ x[a], 8);                                               \
  x[c] += x[d];                                                                \
  x[b] = ROTL32(x[b] ^ x[c], 7);

static void chacha20_block(uint32_t out[16], uint32_t const in[16]) {
  int i;
  uint32_t x[16];
  for (i = 0; i < 16; ++i)
    x[i] = in[i];
  for (i = 0; i < 10; ++i) {
    QUARTERROUND(x, 0, 4, 8, 12)
    QUARTERROUND(x, 1, 5, 9, 13)
    QUARTERROUND(x, 2, 6, 10, 14)
    QUARTERROUND(x, 3, 7, 11, 15)
    QUARTERROUND(x, 0, 5, 10, 15)
    QUARTERROUND(x, 1, 6, 11, 12)
    QUARTERROUND(x, 2, 7, 8, 13)
    QUARTERROUND(x, 3, 4, 9, 14)
  }
  for (i = 0; i < 16; ++i)
    out[i] = x[i] + in[i];
}

void chacha20_encrypt(uint8_t *data, size_t len, const uint32_t key[8],
                      uint64_t nonce, uint32_t counter) {
  uint32_t state[16] = {0x61707865,
                        0x3320646e,
                        0x79622d32,
                        0x6b206574,
                        key[0],
                        key[1],
                        key[2],
                        key[3],
                        key[4],
                        key[5],
                        key[6],
                        key[7],
                        counter,
                        (uint32_t)(nonce),
                        (uint32_t)(nonce >> 32),
                        0};
  uint32_t block[16];
  uint8_t *out = (uint8_t *)block;
  size_t i;

  while (len > 0) {
    chacha20_block(block, state);
    state[12]++;
    size_t n = len < 64 ? len : 64;
    for (i = 0; i < n; i++)
      data[i] ^= out[i];
    data += n;
    len -= n;
  }
}

#define ROTL(x, b) (uint64_t)(((x) << (b)) | ((x) >> (64 - (b))))
#define SIPROUND                                                               \
  do {                                                                         \
    v0 += v1;                                                                  \
    v1 = ROTL(v1, 13);                                                         \
    v1 ^= v0;                                                                  \
    v0 = ROTL(v0, 32);                                                         \
    v2 += v3;                                                                  \
    v3 = ROTL(v3, 16);                                                         \
    v3 ^= v2;                                                                  \
    v0 += v3;                                                                  \
    v3 = ROTL(v3, 21);                                                         \
    v3 ^= v0;                                                                  \
    v2 += v1;                                                                  \
    v1 = ROTL(v1, 17);                                                         \
    v1 ^= v2;                                                                  \
    v2 = ROTL(v2, 32);                                                         \
  } while (0)

uint64_t siphash24(const uint8_t *in, size_t inlen, const uint64_t k[2]) {
  uint64_t v0 = 0x736f6d6570736575ULL ^ k[0];
  uint64_t v1 = 0x646f72616e646f6dULL ^ k[1];
  uint64_t v2 = 0x6c7967656e657261ULL ^ k[0];
  uint64_t v3 = 0x7465646279746573ULL ^ k[1];
  uint64_t m;
  const uint8_t *end = in + (inlen & ~7);
  int left = inlen & 7;
  uint64_t b = ((uint64_t)inlen) << 56;

  for (; in != end; in += 8) {
    memcpy(&m, in, 8);
    v3 ^= m;
    SIPROUND;
    SIPROUND;
    v0 ^= m;
  }
  m = 0;
  switch (left) {
  case 7:
    m |= ((uint64_t)in[6]) << 48; // fallthrough
  case 6:
    m |= ((uint64_t)in[5]) << 40; // fallthrough
  case 5:
    m |= ((uint64_t)in[4]) << 32; // fallthrough
  case 4:
    m |= ((uint64_t)in[3]) << 24; // fallthrough
  case 3:
    m |= ((uint64_t)in[2]) << 16; // fallthrough
  case 2:
    m |= ((uint64_t)in[1]) << 8; // fallthrough
  case 1:
    m |= ((uint64_t)in[0]);
    break;
  case 0:
    break;
  }
  b |= m;
  v3 ^= b;
  SIPROUND;
  SIPROUND;
  v0 ^= b;
  v2 ^= 0xff;
  SIPROUND;
  SIPROUND;
  SIPROUND;
  SIPROUND;
  return v0 ^ v1 ^ v2 ^ v3;
}
