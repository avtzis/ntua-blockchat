from Crypto.PublicKey import RSA

class Wallet:
  def __init__(self):
    self.private_key, self.public_key = self.generate_key()

  def generate_key(self):
    # Generate a random RSA key
    key = RSA.generate(2048)
    private_key = key.export_key()
    public_key = key.publickey().export_key()
    return private_key.decode(), public_key.decode()
