import struct

def rotl(x, b): return ((x << b) | (x >> (64 - b))) & 0xFFFFFFFFFFFFFFFF

def siphash24(key: bytes, data: bytes) -> bytes:
    k0, k1 = struct.unpack("<QQ", key)
    v0 = 0x736f6d6570736575 ^ k0; v1 = 0x646f72616e646f6d ^ k1
    v2 = 0x6c7967656e657261 ^ k0; v3 = 0x7465646279746573 ^ k1

    def sipround():
        nonlocal v0, v1, v2, v3
        v0=(v0+v1)&0xFFFFFFFFFFFFFFFF; v1=rotl(v1,13); v1^=v0; v0=rotl(v0,32)
        v2=(v2+v3)&0xFFFFFFFFFFFFFFFF; v3=rotl(v3,16); v3^=v2
        v0=(v0+v3)&0xFFFFFFFFFFFFFFFF; v3=rotl(v3,21); v3^=v0
        v2=(v2+v1)&0xFFFFFFFFFFFFFFFF; v1=rotl(v1,17); v1^=v2; v2=rotl(v2,32)

    length = len(data)
    for i in range(0, length - (length % 8), 8):
        m = struct.unpack("<Q", data[i:i+8])[0]
        v3 ^= m; sipround(); sipround(); v0 ^= m

    left = length % 8
    b = (length << 56) & 0xFFFFFFFFFFFFFFFF
    if left > 0: b |= int.from_bytes(data[length - left:], 'little')

    v3 ^= b; sipround(); sipround(); v0 ^= b
    v2 ^= 0xff; sipround(); sipround(); sipround(); sipround()
    
    return struct.pack("<Q", v0 ^ v1 ^ v2 ^ v3)
