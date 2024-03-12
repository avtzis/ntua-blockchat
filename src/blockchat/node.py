import json
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization

from wallet import Wallet
from block import Block
from transaction import Transaction

class Node:
  def __init__(self):
    self.id = None
    self.wallet = Wallet()
    self.balance = 0
    self.nonce = 0
    self.blockchain = None
    self.stake = 0
    self.socket = None

  def create_transaction(self, receiver_address, type_of_transaction, value):
    transaction = {
      'sender_address': self.wallet.public_key,
      'receiver_address': receiver_address,
      'type_of_transaction': type_of_transaction,
      'value': value,
      'nonce': self.nonce,
    }

    transaction['signature'] = self.sign_transaction(transaction)

    return Transaction(**transaction)

  def sign_transaction(self, transaction):
    transaction_bytes = json.dumps(transaction).encode()

    signature = self.wallet.private_key.sign(
      transaction_bytes,
      padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()),
        salt_length=padding.PSS.MAX_LENGTH
      ),
      hashes.SHA256()
    )

    return signature

  def execute_transaction(self, transaction):
    pass

  def broadcast_transaction(self, transaction):
    pass

  def verify_signature(self, transaction):
    signature = transaction.pop('signature')
    transaction_bytes = json.dumps(transaction).encode()
    public_key = serialization.load_pem_public_key(transaction['sender_address'])

    try:
      public_key.verify(
        signature,
        transaction_bytes,
        padding.PSS(
          mgf=padding.MGF1(hashes.SHA256()),
          salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
      )
      return True
    except Exception as e:
      return False

  def validate_transaction(self, transaction):
    sender_key, receiver_key = transaction['sender_address'], transaction['receiver_address']
    sender = next((node for node in self.blockchain.nodes if node['key'] == sender_key), None)
    receiver = next((node for node in self.blockchain.nodes if node['key'] == receiver_key), None)
    if not sender or not receiver:
      return False

    if not self.verify_signature(transaction):
      return False

    available_balance = sender['balance'] - sender['stake']
    if transaction['type_of_transaction'] == 'coins':
      total_cost = (1 + self.blockchain.fee_rate) * transaction['value']
      if available_balance < total_cost:
        return False

    if transaction['type_of_transaction'] == 'message':
      if available_balance < len(transaction['value']):
        return False

    return True


class Bootstrap(Node):
  def __init__(self, blockchain):
    super().__init__()

    self.blockchain = blockchain
    self.id = 0

  def create_genesis_block(self, nodes_count):
    # Create the initial transaction
    transaction = Transaction(
      '0',
      self.wallet.get_address(),
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

  def add_node(self, id, address, port, key, balance=0, stake=0):
    self.blockchain.nodes.append({
      'id': id,
      'address': address,
      'port': port,
      'key': key,
      'balance': balance,
      'stake': stake
    })
