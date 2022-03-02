import hmac
from typing import Union

import argon2
from argon2.exceptions import InvalidHash, VerificationError, VerifyMismatchError
from flask import Flask, current_app

from .exceptions import ShortPassword, CommonPassword
from .pwnedpasswords import haveibeenpwned

PASSWORD_CHECK_COMMON = True
PASSWORD_ENCODING = "utf-8"
PASSWORD_MIN_LENGTH = 8
_HASH_TYPE = "sha256"


def _bytes(s: Union[bytes, str], encoding) -> bytes:
    """
    Ensure *s* is a bytes string.
    """
    if isinstance(s, bytes):
        return s
    return s.encode(encoding)


def _str(s: Union[bytes, str], encoding) -> str:
    """
    Ensure *s* is a string.
    """
    if isinstance(s, str):
        return s
    return s.decode(encoding)


def _pepper(password: Union[str, bytes]) -> bytes:
    encoding = current_app.config["PASSWORD_ENCODING"]
    password = _bytes(password, encoding)
    secret = current_app.config["PASSWORD_SECRET"]
    if secret is not None:
        secret = _bytes(secret, encoding)
        password = hmac.digest(secret, password, _HASH_TYPE)
    return password


class Password:
    """
    The purpose is to provide a simple interface for overriding Werkzeug's
    built-in password hashing utilities.
    """

    def __init__(self, app: Flask = None) -> None:
        self.ph = argon2.PasswordHasher()
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        app.config.setdefault("PASSWORD_CHECK_COMMON", PASSWORD_CHECK_COMMON)
        app.config.setdefault("PASSWORD_ENCODING", PASSWORD_ENCODING)
        app.config.setdefault("PASSWORD_MIN_LENGTH", PASSWORD_MIN_LENGTH)
        app.config.setdefault("PASSWORD_SECRET", None)

    def generate_password_hash(self, password: Union[str, bytes]) -> str:
        """
        Hash *password* and return an encoded hash.
        """
        min_length = current_app.config["PASSWORD_MIN_LENGTH"]
        if len(password) < min_length:
            raise ShortPassword(
                f"Password must be at least {min_length} characters long."
            )
        encoding = current_app.config["PASSWORD_ENCODING"]
        if current_app.config["PASSWORD_CHECK_COMMON"] and haveibeenpwned(
            _str(password, encoding)
        ):
            raise CommonPassword("Given password is a common one.")
        return self.ph.hash(_pepper(password))

    def check_password_hash(
        self, pw_hash: Union[str, bytes], password: Union[str, bytes]
    ) -> bool:
        """
        Verify that *password* matches *pw_hash*.
        """
        try:
            return self.ph.verify(pw_hash, _pepper(password))
        except (VerifyMismatchError, VerificationError, InvalidHash):
            return False

    def check_needs_rehash(self, pw_hash: str) -> bool:
        """
        Check whether *pw_hash* needs rehashing.

        Whenever the defaults change, you should rehash your passwords at
        the next opportunity. The common approach is to do that whenever a
        user logs in, since that should be the only time when you have access
        to the cleartext password.

        Therefore it's best practice to check, and if necessary rehash,
        passwords after each successful authentication.
        """
        return self.ph.check_needs_rehash(pw_hash)
