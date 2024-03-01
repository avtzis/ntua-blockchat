class Transaction:
  def __init__(self, sender_address, receiver_address, type_of_transaction, value, nonce, signature):
    self.sender_address = sender_address
    self.receiver_address = receiver_address
    self.type_of_transaction = type_of_transaction
    self.value = value
    self.nonce = nonce
    self.signature = signature

  def __str__(self):
    return f"{self.sender_address}:{self.receiver_address}:{self.type_of_transaction}:{self.value}"


  # def __repr__(self):
  #   return f"Transaction: {self.sender} -> {self.receiver} : {self.amount} : {self.timestamp}"
