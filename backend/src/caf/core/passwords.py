"""
Heširanje lozinki — Argon2id (RFC 9106 preporuka), preko `argon2-cffi`.

Security by Design (CLAUDE.md Sekcija 3, pravilo 4): nema sopstvene
kriptografije, nema zastarjelih biblioteka (passlib nije održavan).
`PasswordHasher` default parametri su OWASP-usklađeni; `check_needs_rehash`
omogućava tihu nadogradnju parametara pri sledećem uspješnom loginu.
"""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

_hasher = PasswordHasher()


def hash_password(plain: str) -> str:
    return _hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """
    True samo ako lozinka odgovara hešu. Svaki drugi ishod (pogrešna
    lozinka, korumpiran/nepoznat heš) vraća False — pozivalac NE dobija
    razlog, da odgovor ne otkriva stanje naloga.
    """
    try:
        return _hasher.verify(hashed, plain)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(hashed: str) -> bool:
    try:
        return _hasher.check_needs_rehash(hashed)
    except InvalidHashError:
        return True
