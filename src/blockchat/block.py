import hashlib
import time

class Block:
  def __init__(self, index, validator, transactions, previous_hash):
    self.index = index
    self.timestamp = time.time()
    self.validator = validator
    self.transactions = transactions
    self.previous_hash = previous_hash

    self.hash = self.calculate_hash()

  def __print__(self):
    return {
      'index': self.index,
      'timestamp': self.timestamp,
      'validator': self.validator,
      'transactions': self.transactions,
      'previous_hash': self.previous_hash,
      'hash': self.hash
    }

  def calculate_hash(self):
    block_data = (
      str(self.index)
      + ':' + str(self.timestamp)
      + ':' + str(self.validator)
      + ':'.join(self.transactions)
      + ':' + str(self.previous_hash)
    )

    return hashlib.sha256(block_data).hexdigest()

