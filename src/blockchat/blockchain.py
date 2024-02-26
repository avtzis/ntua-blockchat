import datetime

from block import Block

class Blockchain:
  def __init__(self, chain=None):
    self.chain = chain or [self.create_genesis_block()]

  def create_genesis_block(self):
    return Block(0, "1", "Genesis Block", "0")

  def add_block(self, block):
    self.chain.append(block)

  def get_last_block(self):
    return self.chain[-1]

  def is_valid(self):
    for i in range(1, len(self.chain)):
      prev_block = self.chain[i-1]
      curr_block = self.chain[i]

      if curr_block.hash != curr_block.calculate_hash():
        return False

      if curr_block.prev_hash != prev_block.hash:
        return False

    return True

  def __str__(self):
    return str([str(block) for block in self.chain])
