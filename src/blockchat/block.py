import hashlib
import json
from datetime import datetime

class Block:
  def __init__(self, index, validator, transactions, previous_hash, timestamp=None, hash=None):
    self.index = index
    self.timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f') if timestamp is None else timestamp
    self.validator = validator
    self.transactions = transactions
    self.previous_hash = previous_hash

    self.hash = self.calculate_hash() if hash is None else hash

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
    block_data = json.dumps({
      'index': self.index,
      'timestamp': self.timestamp,
      'validator': self.validator,
      'transactions': [dict(transaction) for transaction in self.transactions],
      'previous_hash': self.previous_hash
    })

    return hashlib.sha256(block_data.encode()).hexdigest()
