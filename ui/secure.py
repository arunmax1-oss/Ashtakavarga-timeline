"""Passphrase encryption for saved profiles kept in the page link.

The link holds "v2." + base64(salt + Fernet token). The key is derived from the passphrase with
PBKDF2-HMAC-SHA256, so without the passphrase the link reveals nothing about the people saved in it.
"""
import base64
import os

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

PREFIX = "v2."
ITERATIONS = 390_000
MIN_LENGTH = 8


def _key(passphrase, salt):
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITERATIONS)
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))


def encrypt(text, passphrase):
    salt = os.urandom(16)
    token = Fernet(_key(passphrase, salt)).encrypt(text.encode())
    return PREFIX + base64.urlsafe_b64encode(salt + token).decode()


def decrypt(blob, passphrase):
    """Plain text, or ValueError if the passphrase is wrong or the link is damaged."""
    if not blob.startswith(PREFIX):
        raise ValueError("not an encrypted link")
    try:
        raw = base64.urlsafe_b64decode(blob[len(PREFIX):].encode())
        return Fernet(_key(passphrase, raw[:16])).decrypt(raw[16:]).decode()
    except (InvalidToken, ValueError, TypeError) as exc:
        raise ValueError("wrong passphrase or damaged link") from exc


def is_encrypted(blob):
    return bool(blob) and blob.startswith(PREFIX)
