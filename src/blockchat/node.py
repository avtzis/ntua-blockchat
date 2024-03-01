from wallet import Wallet
from block import Block
from transaction import Transaction

class Node:
  def __init__(self):
    self.id = None
    self.wallet = Wallet()
    self.BCC = 0
    self.nonce = 0
    self.blockchain = None

class Bootstrap(Node):
  def __init__(self, blockchain):
    super().__init__()

    self.blockchain = blockchain
    self.id = 0
    self.nodes = []

  def create_genesis_block(self):
    # Create the transaction
    transaction = Transaction(
      '0',
      self.wallet.public_key,
      'coins',
      self.nonce,
      None
    )

    # Increment the nonce
    self.nonce += 1

    # Create the genesis block
    genesis_block = Block(0, 0, [transaction], '1')

    # Add the block to the blockchain
    self.blockchain.add_block(genesis_block)

  def add_node(self, port, key):
    self.nodes.append((port, key))
