class Wallet:
  def __init__(self, private_key, public_key):
    self.private_key = private_key
    self.public_key = public_key
    self.address = self.generate_address()

  def generate_address(self):
    return sha256(self.public_key)

