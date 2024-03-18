"""A module for the Blockchain class.

This module contains the Blockchain class, which is used to represent the
blockchain of the network.
"""

from block import Block

class Blockchain:
  """A class to represent the blockchain of the network.

  Attributes:
    chain (list): A list of blocks in the blockchain.
    block_capacity (int): The maximum number of transactions per block.
    block_index (int): The index of the current block.
    nodes (list): A list of nodes in the network.
    fee_rate (float): The fee rate for transactions.

  Methods:
    add_block: Add a block to the blockchain.
    get_last_block: Get the last block in the blockchain.
  """

  def __init__(self, block_capacity, chain=[], block_index=0, nodes=[]):
    """Initializes a new instance of Blockchain.

    Args:
      block_capacity (int): The maximum number of transactions per block.
      chain (list, optional): A list of blocks in the blockchain. Defaults to [].
      block_index (int, optional): The index of the current block. Defaults to 0.
      nodes (list, optional): A list of nodes in the network. Defaults to [].
    """

    self.chain = [Block(**block) for block in chain]
    self.block_capacity = block_capacity
    self.block_index = block_index
    self.nodes = nodes
    self.fee_rate = 0.03

  def add_block(self, block):
    """Adds a block to the blockchain.

    Args:
      block (Block): The block to add to the blockchain.
    """

    self.chain.append(block)
    self.block_index += 1

  def get_last_block(self):
    """Gets the last block in the blockchain.

    Returns:
      Block: The last block in the blockchain.
    """

    return self.chain[-1]

  def __str__(self):
    return str([str(block) for block in self.chain])

  def __print__(self):
    return str(self)

  def __iter__(self):
    yield 'block_capacity', self.block_capacity
    yield 'block_index', self.block_index
    yield 'chain', [dict(block) for block in self.chain]
    yield 'nodes', self.nodes
