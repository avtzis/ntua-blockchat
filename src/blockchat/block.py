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
    return str(self.__dict__())

  def __dict__(self):
    return {
      'index': self.index,
      'timestamp': self.timestamp,
      'validator': self.validator,
      'transactions': self.transactions,
      'previous_hash': self.previous_hash,
      'hash': self.hash
    }

  def __str__(self):
    return str({
      'index': self.index,
      'timestamp': self.timestamp,
      'validator': self.validator,
      'transactions': [transaction.__dict__() for transaction in self.transactions],
      'previous_hash': self.previous_hash,
      'hash': self.hash
    })

  # def __iter__

  def calculate_hash(self):
    block_data = (
      str(self.index)
      + ':' + str(self.timestamp)
      + ':' + str(self.validator)
      + ':'.join(map(str, self.transactions))
      + ':' + str(self.previous_hash)
    )

    return hashlib.sha256(block_data.encode()).hexdigest()

