import struct


def ROTL32(v, c):
    return ((v << c) & 0xFFFFFFFF) | (v >> (32 - c))


def quarter_round(x, a, b, c, d):
    x[a] = (x[a] + x[b]) & 0xFFFFFFFF
    x[d] = ROTL32(x[d] ^ x[a], 16)
    x[c] = (x[c] + x[d]) & 0xFFFFFFFF
    x[b] = ROTL32(x[b] ^ x[c], 12)
    x[a] = (x[a] + x[b]) & 0xFFFFFFFF
    x[d] = ROTL32(x[d] ^ x[a], 8)
    x[c] = (x[c] + x[d]) & 0xFFFFFFFF
    x[b] = ROTL32(x[b] ^ x[c], 7)


def chacha20_block(key, nonce, counter):
    x = [
        0x61707865,
        0x3320646E,
        0x79622D32,
        0x6B206574,
        key[0],
        key[1],
        key[2],
        key[3],
        key[4],
        key[5],
        key[6],
        key[7],
        counter,
        nonce & 0xFFFFFFFF,
        (nonce >> 32) & 0xFFFFFFFF,
        0,
    ]
    initial = list(x)
    for _ in range(10):
        quarter_round(x, 0, 4, 8, 12)
        quarter_round(x, 1, 5, 9, 13)
        quarter_round(x, 2, 6, 10, 14)
        quarter_round(x, 3, 7, 11, 15)
        quarter_round(x, 0, 5, 10, 15)
        quarter_round(x, 1, 6, 11, 12)
        quarter_round(x, 2, 7, 8, 13)
        quarter_round(x, 3, 4, 9, 14)
    return [(x[i] + initial[i]) & 0xFFFFFFFF for i in range(16)]


def chacha20_encrypt(data, key_bytes, nonce, counter=0):
    key = struct.unpack("<8I", key_bytes)
    out = bytearray()
    for i in range(0, len(data), 64):
        block = struct.pack("<16I", *chacha20_block(key, nonce, counter))
        counter += 1
        chunk = data[i : i + 64]
        out.extend(b ^ k for b, k in zip(chunk, block))
    return bytes(out)
