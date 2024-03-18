"""A module for the Wallet class.

This module contains the Wallet class, which is used to create a
wallet for a node.
"""

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

class Wallet:
  """A class to represent a node wallet.

  Attributes:
    private_key (cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey): The private key of the wallet.
    public_key (cryptography.hazmat.primitives.asymmetric.rsa.RSAPublicKey): The public key of the wallet.

  Methods:
    generate_key: Generate a private and public key pair.
    get_address: Get the public key in PEM format.
  """

  def __init__(self):
    """Initializes a new instance of Wallet."""

    self.private_key, self.public_key = self.generate_key()

  @staticmethod
  def generate_key():
    """Generates a private and public key pair.

    This method generates a private and public key pair using the RSA algorithm.

    Returns:
      cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey: The private key.
      cryptography.hazmat.primitives.asymmetric.rsa.RSAPublicKey: The public key.
    """

    private_key = rsa.generate_private_key(
      public_exponent=65537,
      key_size=2048
    )
    public_key = private_key.public_key()

    return private_key, public_key

  def get_address(self):
    """Gets the public key in PEM format.

    Returns:
      str: The public key in PEM format.
    """

    public_pem = self.public_key.public_bytes(
      encoding=serialization.Encoding.PEM,
      format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return public_pem.decode()
