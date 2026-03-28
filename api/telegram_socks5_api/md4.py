from __future__ import annotations

import struct


def _lrot(value: int, shift: int) -> int:
    value &= 0xFFFFFFFF
    return ((value << shift) | (value >> (32 - shift))) & 0xFFFFFFFF


def md4(data: bytes) -> bytes:
    message = bytearray(data)
    bit_len = (8 * len(message)) & 0xFFFFFFFFFFFFFFFF
    message.append(0x80)
    while len(message) % 64 != 56:
        message.append(0)
    message += struct.pack("<Q", bit_len)

    a = 0x67452301
    b = 0xEFCDAB89
    c = 0x98BADCFE
    d = 0x10325476

    def f(x: int, y: int, z: int) -> int:
        return (x & y) | (~x & z)

    def g(x: int, y: int, z: int) -> int:
        return (x & y) | (x & z) | (y & z)

    def h(x: int, y: int, z: int) -> int:
        return x ^ y ^ z

    for offset in range(0, len(message), 64):
        x = list(struct.unpack("<16I", message[offset : offset + 64]))
        aa, bb, cc, dd = a, b, c, d

        # Round 1
        s = (3, 7, 11, 19)
        for i in range(0, 16, 4):
            a = _lrot((a + f(b, c, d) + x[i]) & 0xFFFFFFFF, s[0])
            d = _lrot((d + f(a, b, c) + x[i + 1]) & 0xFFFFFFFF, s[1])
            c = _lrot((c + f(d, a, b) + x[i + 2]) & 0xFFFFFFFF, s[2])
            b = _lrot((b + f(c, d, a) + x[i + 3]) & 0xFFFFFFFF, s[3])

        # Round 2
        s = (3, 5, 9, 13)
        idx = [0, 4, 8, 12, 1, 5, 9, 13, 2, 6, 10, 14, 3, 7, 11, 15]
        for i in range(0, 16, 4):
            a = _lrot((a + g(b, c, d) + x[idx[i]] + 0x5A827999) & 0xFFFFFFFF, s[0])
            d = _lrot((d + g(a, b, c) + x[idx[i + 1]] + 0x5A827999) & 0xFFFFFFFF, s[1])
            c = _lrot((c + g(d, a, b) + x[idx[i + 2]] + 0x5A827999) & 0xFFFFFFFF, s[2])
            b = _lrot((b + g(c, d, a) + x[idx[i + 3]] + 0x5A827999) & 0xFFFFFFFF, s[3])

        # Round 3
        s = (3, 9, 11, 15)
        idx = [0, 8, 4, 12, 2, 10, 6, 14, 1, 9, 5, 13, 3, 11, 7, 15]
        for i in range(0, 16, 4):
            a = _lrot((a + h(b, c, d) + x[idx[i]] + 0x6ED9EBA1) & 0xFFFFFFFF, s[0])
            d = _lrot((d + h(a, b, c) + x[idx[i + 1]] + 0x6ED9EBA1) & 0xFFFFFFFF, s[1])
            c = _lrot((c + h(d, a, b) + x[idx[i + 2]] + 0x6ED9EBA1) & 0xFFFFFFFF, s[2])
            b = _lrot((b + h(c, d, a) + x[idx[i + 3]] + 0x6ED9EBA1) & 0xFFFFFFFF, s[3])

        a = (a + aa) & 0xFFFFFFFF
        b = (b + bb) & 0xFFFFFFFF
        c = (c + cc) & 0xFFFFFFFF
        d = (d + dd) & 0xFFFFFFFF

    return struct.pack("<4I", a, b, c, d)


def nt_hash(password: str) -> str:
    return md4(password.encode("utf-16le")).hex().upper()
