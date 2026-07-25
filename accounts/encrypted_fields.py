from django.db import models
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


class EncryptedCharField(models.CharField):

    def get_cipher(self):
        return Fernet(settings.FIELD_ENCRYPTION_KEY.encode())

    def get_prep_value(self, value):
        """
        Encrypt value before saving it to the database.
        """
        if value is None or value == "":
            return value

        # Avoid encrypting an already encrypted value
        if self.is_encrypted(value):
            return value

        cipher = self.get_cipher()
        return cipher.encrypt(str(value).encode()).decode()

    def from_db_value(self, value, expression, connection):
        """
        Decrypt value when retrieving it from the database.
        """
        if value is None or value == "":
            return value

        cipher = self.get_cipher()

        try:
            return cipher.decrypt(value.encode()).decode()
        except (InvalidToken, ValueError, TypeError):
            # Allows existing plaintext data to remain readable
            # until we run the data encryption migration.
            return value

    def to_python(self, value):
        """
        Convert database value to Python value.
        """
        if value is None or value == "":
            return value

        if isinstance(value, str):
            cipher = self.get_cipher()

            try:
                return cipher.decrypt(value.encode()).decode()
            except (InvalidToken, ValueError, TypeError):
                return value

        return value

    def is_encrypted(self, value):
        """
        Check whether the value is already encrypted.
        """
        if not value:
            return False

        cipher = self.get_cipher()

        try:
            cipher.decrypt(str(value).encode())
            return True
        except (InvalidToken, ValueError, TypeError):
            return False