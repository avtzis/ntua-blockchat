"""A module for the Transaction class.

This module contains the Transaction class, which is used to represent a
transaction in the blockchain.
"""

import json

class Transaction:
  """A class to represent a transaction in the blockchain.

  Attributes:
    uuid (str): The UUID of the transaction.
    sender_address (str): The address of the sender.
    receiver_address (str): The address of the receiver.
    timestamp (str): The timestamp of the transaction.
    type_of_transaction (str): The type of the transaction.
    value (float): The value of the transaction.
    nonce (int): The nonce of the transaction.
    signature (str): The signature of the transaction.
  """

  def __init__(self, uuid, sender_address, receiver_address, timestamp, type_of_transaction, value, nonce, signature):
    """Initializes a new instance of Transaction.

    Args:
      uuid (str): The UUID of the transaction.
      sender_address (str): The address of the sender.
      receiver_address (str): The address of the receiver.
      timestamp (str): The timestamp of the transaction.
      type_of_transaction (str): The type of the transaction.
      value (float): The value of the transaction.
      nonce (int): The nonce of the transaction.
      signature (str): The signature of the transaction.
    """

    self.uuid = uuid
    self.sender_address = sender_address
    self.receiver_address = receiver_address
    self.timestamp = timestamp
    self.type_of_transaction = type_of_transaction
    self.value = value
    self.nonce = nonce
    self.signature = signature

  def __str__(self):
    return json.dumps(dict(self))

  def __iter__(self):
    yield 'uuid', self.uuid
    yield 'sender_address', self.sender_address
    yield 'receiver_address', self.receiver_address
    yield 'timestamp', self.timestamp
    yield 'type_of_transaction', self.type_of_transaction
    yield 'value', self.value
    yield 'nonce', self.nonce
    yield 'signature', self.signature
