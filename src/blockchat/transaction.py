class Transaction:
  def __init__(self, sender, receiver, amount, timestamp):
    self.sender = sender
    self.receiver = receiver
    self.amount = amount
    self.timestamp = timestamp

  def __str__(self):
    return f"Transaction: {self.sender} -> {self.receiver} : {self.amount} : {self.timestamp}"

  def __repr__(self):
    return f"Transaction: {self.sender} -> {self.receiver} : {self.amount} : {self.timestamp}"
