from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

class Wallet:
  def __init__(self):
    self.private_key, self.public_key = self.generate_key()

  @staticmethod
  def generate_key():
    private_key = rsa.generate_private_key(
      public_exponent=65537,
      key_size=2048
    )
    public_key = private_key.public_key()

    return private_key, public_key

  def get_address(self):
    public_pem = self.public_key.public_bytes(
      encoding=serialization.Encoding.PEM,
      format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return public_pem.decode()
