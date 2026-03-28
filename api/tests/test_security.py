from __future__ import annotations

from telegram_socks5_api.security import hash_admin_password, hash_proxy_password, verify_admin_password, verify_proxy_password
from telegram_socks5_api.md4 import nt_hash


def test_nt_hash_known_value():
    assert nt_hash("password") == "8846F7EAEE8FB117AD06BDD830B7586C"


def test_admin_password_roundtrip():
    encoded = hash_admin_password("s3cret")
    assert encoded.startswith("pbkdf2_sha256$")
    assert verify_admin_password("s3cret", encoded)
    assert not verify_admin_password("wrong", encoded)


def test_proxy_password_roundtrip():
    encoded = hash_proxy_password("s3cret")
    assert encoded.startswith("nt$")
    assert verify_proxy_password("s3cret", encoded)
    assert not verify_proxy_password("wrong", encoded)
