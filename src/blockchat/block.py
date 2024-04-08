"""A module for the Block class.

This module contains the Block class, which is used to represent a
block in the blockchain.
"""

import hashlib
import json
from datetime import datetime

from blockchat.transaction import Transaction

class Block:
  """A class to represent a block in the blockchain.

  Attributes:
    index (int): The index of the block.
    timestamp (str): The timestamp of the block.
    validator (str): The validator of the block.
    transactions (list): A list of transactions in the block.
    previous_hash (str): The hash of the previous block.
    hash (str): The hash of the block.

  Methods:
    calculate_hash: Calculate the hash of the block.
  """

  def __init__(self, index, validator, transactions, previous_hash, timestamp=None, hash=None):
    """Initializes a new instance of Block.

    Args:
      index (int): The index of the block.
      validator (str): The validator of the block.
      transactions (list): A list of transactions in the block.
      previous_hash (str): The hash of the previous block.
      timestamp (str, optional): The timestamp of the block. Defaults to None.
      hash (str, optional): The hash of the block. Defaults to None.
    """

    self.index = index
    self.timestamp = datetime.now().isoformat() if timestamp is None else timestamp
    self.validator = validator
    self.transactions = [Transaction(**dict(transaction)) for transaction in transactions]
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
