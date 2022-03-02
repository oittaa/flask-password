# flask-password

flask-password is a Flask extension that provides modern password hashing utilities for your Flask app.

[![CI](https://github.com/oittaa/flask-password/actions/workflows/main.yml/badge.svg)](https://github.com/oittaa/flask-password/actions/workflows/main.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Installation

Install the extension with the following command:

```
pip install git+https://github.com/oittaa/flask-password.git
```

## Usage

To use the extension simply import the class wrapper and pass the Flask app object back to it.

```
from flask import Flask
from flask_password import Password

app = Flask(__name__)
pw = Password(app)
```

When using an application factory this extension can be initialized by the `init_app()` function.

The following Flask Configs are automatically used by `init_app()`:

|Variable Name | Description |
|---|---|
|`PASSWORD_CHECK_COMMON`|Whether to check if the password given to `generate_password_hash()` is a commonly used one from [Have I Been Pwned](https://haveibeenpwned.com/Passwords) using a k-Anonymity model that allows a password to be searched for by partial hash. Raises `CommonPassword` exception if the password is a common one. Default `True`|
|`PASSWORD_MIN_LENGTH`|Defines the minumum length of the password given to `generate_password_hash()`. Raises `ShortPassword` exception if the password is shorter than that. Default `8`|
|`PASSWORD_SECRET`|Defines a secret (also known as a pepper) added to the input during hashing. Default `None`|
|`PASSWORD_ENCODING`|The underlying hashing library expects bytes. If a string is passed to the methods, it will be encoded using this encoding. Default `utf-8`|

Completely working example with the available methods.
```
import secrets
from flask import Flask
from flask_password import Password, exceptions

pw = Password()
app = Flask(__name__)
pw.init_app(app)


password = secrets.token_urlsafe()
print(f"{password=}")

# This example doesn't actually start a Flask server, but it still needs the
# Flask context for the methods to work properly.
with app.app_context():
    pw_hash = pw.generate_password_hash(password)
    assert pw.check_password_hash(pw_hash, password) == True
    print(f"{pw_hash=}")

    if pw.check_needs_rehash(pw_hash):
        print("Hash's parameters outdated.")
    else:
        print("No need to change hash.")

    try:
        pw_hash = pw.generate_password_hash("short")
    except exceptions.ShortPassword as err:
        print(err)

    try:
        pw_hash = pw.generate_password_hash("P@ssword1")
    except exceptions.CommonPassword as err:
        print(err)

```

Login example
```
from flask_password import Password


pw = Password(app)


def login(db, user, password):
    pw_hash = db.get_password_hash_for_user(user)

    # Verify password, returns False if wrong.
    if not pw.check_password_hash(pw_hash, password):
        return False

    # Now that we have the cleartext password,
    # check the hash's parameters and if outdated,
    # rehash the user's password in the database.
    if pw.check_needs_rehash(pw_hash):
        db.set_password_hash_for_user(user, pw.generate_password_hash(password))

    return True
```
