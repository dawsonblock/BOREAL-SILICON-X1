#!/usr/bin/env python3
import time, struct, spidev
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from siphash import siphash24
from chacha20 import chacha20_encrypt

# 128-bit Shared Secret
MAC_KEY = struct.pack("<QQ", 0xA3B1C2D3E4F56789, 0x1020304050607080)
# 256-bit ChaCha20 Cipher Key
CHACHA_KEY = struct.pack(
    "<8I",
    0x01020304,
    0x05060708,
    0x090A0B0C,
    0x0D0E0F10,
    0x11121314,
    0x15161718,
    0x191A1B1C,
    0x1D1E1F20,
)

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 10_000_000
spi.mode = 0
SEQ = 0


def send_to_boreal(intent_id, conf_q15, aux_data):
    global SEQ
    SEQ += 1

    # Encrypt-then-MAC payload
    aux = (aux_data + [0] * 18)[:18]  # Pad to 18 elements

    plaintext = struct.pack("<HH18h", intent_id, conf_q15, *aux)
    ciphertext = chacha20_encrypt(plaintext, CHACHA_KEY, SEQ, 0)

    header = struct.pack(
        "<IHHII", 0xB0A1E1A1, 1, 1, SEQ, int(time.time() * 1000) & 0xFFFFFFFF
    )

    payload = header + ciphertext

    # Cryptographic MAC + SPI Frame
    mac = siphash24(MAC_KEY, payload)
    frame = bytes([0x01, 64]) + payload + mac
    spi.xfer2(list(frame))


if __name__ == "__main__":
    while True:
        # [INSERT AI INFERENCE HERE]
        # Example: Model detects a person (Intent 2) with 85% conf (27851)
        send_to_boreal(intent_id=2, conf_q15=27851, aux_data=[30])
        time.sleep(0.02)  # 50 Hz control loop
