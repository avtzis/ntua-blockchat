import hashlib
from datetime import datetime

class Block:
  def __init__(self, index, validator, transactions, previous_hash):
    self.index = index
    self.timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')
    self.validator = validator
    self.transactions = transactions
    self.previous_hash = previous_hash

    self.hash = self.calculate_hash()

  def __print__(self):
    return str(self)

  def __iter__(self):
    yield 'index', self.index
    yield 'timestamp', self.timestamp
    yield 'validator', self.validator
    yield 'transactions', [dict(transaction) for transaction in self.transactions]
    yield 'previous_hash', self.previous_hash
    yield 'hash', self.hash

  def __str__(self):
    return str(dict(self))

  def calculate_hash(self):
    block_data = (
      str(self.index)
      + ':' + str(self.timestamp)
      + ':' + str(self.validator)
      + ':'.join(map(str, self.transactions))
      + ':' + str(self.previous_hash)
    )

    return hashlib.sha256(block_data.encode()).hexdigest()
