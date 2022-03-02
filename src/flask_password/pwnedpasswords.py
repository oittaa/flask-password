"""
This module uses the pwnedpasswords.com v2 API to check passwords in a secure way.
https://en.wikipedia.org/wiki/K-anonymity
The full hash is never transmitted over the wire, only the first 5 characters. The comparison
happens offline. Special thanks to Troy Hunt (@troyhunt) for making this script possible.
"""
from functools import lru_cache
from hashlib import sha1
from urllib.request import Request, urlopen

API_URL = "https://api.pwnedpasswords.com/range/{0}"
HEADERS = {"User-Agent": "Flask-Password"}


@lru_cache
def _download(url: str) -> str:
    req = Request(url=url, headers=HEADERS)
    with urlopen(req) as f:
        res = f.read().decode("utf-8")
    return res


def haveibeenpwned(password: str) -> int:
    """
    This function takes a password string as an input and returns True if the *password*
    appears in PwnedPasswords.
    """
    passhash = sha1(password.encode("utf-8")).hexdigest().upper()
    ph_end = passhash[5:]
    url = API_URL.format(passhash[:5])
    passlist = _download(url)
    for line in passlist.split("\n"):
        larr = line.split(":")
        if larr[0] == ph_end:
            return True
    return False
