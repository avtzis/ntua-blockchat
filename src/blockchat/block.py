import hashlib
import time

class Block:
  def __init__(self, index, previous_hash, transactions, validator):
    self.index = index
    self.previous_hash = previous_hash
    self.timestamp = time.time()
    self.transactions = transactions
    self.validator = validator
    self.hash = self.calculate_hash()

  def __str__(self):
    return str(self.index) + self.previous_hash + str(self.timestamp) + self.transactions + self.hash

  def calculate_hash(self):
    return hashlib.sha256(str(self.index).encode() + self.previous_hash.encode() + str(self.timestamp).encode() + self.transactions.encode()).hexdigest()

  def is_valid(self):
    return self.hash == self.calculate_hash()
