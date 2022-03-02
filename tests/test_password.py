import secrets

import pytest

from flask import Flask
from flask_password import Password, exceptions


TEST_HASH = "$argon2i$v=19$m=16,t=2,p=1$V01KRjBPRER4UHBxcTJHdg$d1sRsp41zBcQmXZICK8E0Q"


@pytest.fixture()
def app():
    app = Flask(__name__)
    app.config.update(
        {
            "PASSWORD_CHECK_COMMON": False,
        }
    )
    yield app


class TestPasswordHasher:
    def test_verify_invalid_hash(self, app):
        """
        Return False if the hash can't be parsed.
        """
        with app.app_context():
            assert Password(app).check_password_hash("$$", b"does not matter") is False

    def test_verify_generate_password_w_secret(self, app):
        """
        Hashes with a secret are valid and can be verified.
        """
        with app.app_context():
            app.config.update(
                {
                    "PASSWORD_CHECK_COMMON": True,
                    "PASSWORD_SECRET": "super secret string",
                    "PASSWORD_ENCODING": "ascii",
                }
            )
            pw = Password()
            pw.init_app(app)
            pw_plain = secrets.token_urlsafe()
            pw_hash = pw.generate_password_hash(pw_plain)
            assert pw.check_password_hash(pw_hash, pw_plain) is True
            app.config.update(
                {
                    "PASSWORD_SECRET": "something different",
                }
            )
            assert pw.check_password_hash(pw_hash, pw_plain) is False

    def test_hash_short_password(self, app):
        """
        If the password is too short, ShortPassword is raised.
        """
        with app.app_context():
            pw = Password(app)
            with pytest.raises(exceptions.ShortPassword):
                pw.generate_password_hash("monkey")

    def test_hash_common_password(self, app):
        """
        If the password is too common, CommonPassword is raised.
        """
        with app.app_context():
            app.config.update(
                {
                    "PASSWORD_CHECK_COMMON": True,
                }
            )
            pw = Password(app)
            with pytest.raises(exceptions.CommonPassword):
                pw.generate_password_hash(b"P@ssword")

    def test_check_needs_rehash_yes(self, app):
        """
        Return True if any of the parameters changes.
        """
        with app.app_context():
            pw = Password(app)
            assert pw.check_needs_rehash(TEST_HASH) is True

    def test_check_needs_rehash_no(self, app):
        """
        Return False if the hash has the correct parameters.
        """
        with app.app_context():
            pw = Password(app)
            pw_plain = secrets.token_urlsafe()
            pw_hash = pw.generate_password_hash(pw_plain)
            assert pw.check_needs_rehash(pw_hash) is False
