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
    self.nodes = []

class Bootstrap(Node):
  def __init__(self, blockchain):
    super().__init__()

    self.blockchain = blockchain
    self.id = 0

  def create_genesis_block(self, nodes_count):
    # Create the transaction
    transaction = Transaction(
      '0',
      self.wallet.public_key,
      'coins',
      1000 * nodes_count,
      self.nonce,
      None
    )

    # Increment the nonce
    self.nonce += 1

    # Create the genesis block
    genesis_block = Block(0, 0, [transaction], '1')

    # Add the block to the blockchain
    self.blockchain.add_block(genesis_block)

  def add_node(self, id, address, port, key, coins=0):
    self.nodes.append({
      'id': id,
      'address': address,
      'port': port,
      'key': key,
      'coins': coins
    })
