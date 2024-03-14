import json

class Transaction:
  def __init__(self, uuid, sender_address, receiver_address, timestamp, type_of_transaction, value, nonce, signature):
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
