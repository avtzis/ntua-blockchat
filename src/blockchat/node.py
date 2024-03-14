import json
import socket
import base64
import random
import uuid
from datetime import datetime
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
    self.balance = 0.0
    self.nonce = 0  #! WHAT TO DO WITH THIS?
    self.blockchain = None
    self.stake = 0
    self.socket = None

    self.current_block = []
    self.current_fees = 0

  @staticmethod
  def send(message, address, port):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
      s.sendto(message.encode(), (address, port))

  def execute_transaction(self, receiver_id, type_of_transaction, value):
    receiver = next((node for node in self.blockchain.nodes if node['id'] == receiver_id), None) if receiver_id != -1 else {'key': '0'}
    if not receiver:
      print(f'[NODE-{self.id}] Invalid receiver')
      return False

    available_balance = self.balance - self.stake
    if type_of_transaction == 'stake':
      if value <= 0 and value > available_balance:
        print(f'[NODE-{self.id}] Insufficient balance or invalid amount to stake')
        return False
    elif type_of_transaction == 'coins':
      total_cost = (1 + self.blockchain.fee_rate) * value
      if total_cost <= 0 and available_balance < total_cost:
        print(f'[NODE-{self.id}] Insufficient balance or invalid amount to transfer')
        return False
    elif type_of_transaction == 'message':
      if not isinstance(value, str) and available_balance < len(value):
        print(f'[NODE-{self.id}] Insufficient balance or invalid message to send')
        return False
    else:
      print(f'[NODE-{self.id}] Invalid transaction type')
      return False

    transaction = self.create_transaction(receiver['key'], type_of_transaction, value)

    print(f'[NODE-{self.id}] Executing transaction: {self.id} -> {receiver_id}, {type_of_transaction}: {value}')

    self.broadcast_transaction(transaction)

    return True

  def create_transaction(self, receiver_address, type_of_transaction, value):
    transaction = {
      'uuid': str(uuid.uuid4()),
      'sender_address': self.wallet.get_address(),
      'receiver_address': receiver_address,
      'timestamp': datetime.now().isoformat(),
      'type_of_transaction': type_of_transaction,
      'value': value,
      'nonce': self.nonce,
    }

    transaction['signature'] = self.sign_transaction(transaction)

    self.nonce += 1

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

    return base64.b64encode(signature).decode()

  def register_transaction(self, transaction):
    sender = next((node for node in self.blockchain.nodes if node['key'] == transaction['sender_address']), None)
    receiver = next((node for node in self.blockchain.nodes if node['key'] == transaction['receiver_address']), None)

    sender['nonce'] += 1

    if transaction['type_of_transaction'] == 'coins':
      total_cost = (1 + self.blockchain.fee_rate) * transaction['value']
      sender['balance'] -= total_cost
      receiver['balance'] += transaction['value']
      self.current_fees += total_cost - transaction['value']

      if sender['id'] == self.id:
        self.balance -= total_cost
      if receiver['id'] == self.id:
        self.balance += transaction['value']

    elif transaction['type_of_transaction'] == 'message':
      sender['balance'] -= len(transaction['value'])
      self.current_fees += len(transaction['value'])

      if sender['id'] == self.id:
        self.balance -= len(transaction['value'])

    elif transaction['type_of_transaction'] == 'stake':
      sender['stake'] += transaction['value']

      if sender['id'] == self.id:
        self.stake += transaction['value']

    print(f'[NODE-{self.id}] Transaction registered successfully: {sender["id"]} -> {receiver["id"] if receiver is not None else "none"}, {transaction["type_of_transaction"]}: {transaction["value"]}')

    self.current_block.append(Transaction(**transaction))
    if len(self.current_block) == self.blockchain.block_capacity:
      self.mine_block()

  def broadcast_transaction(self, transaction):
    message = json.dumps({
      'message_type': 'transaction',
      'transaction': dict(transaction)
    })

    for node in self.blockchain.nodes:
      self.send(message, node['address'], node['port'])

  def receive_transaction(self, transaction):
    if not self.validate_transaction(transaction):
      # print(f'[NODE-{self.id}] Invalid transaction received: {transaction}')
      print(f'[NODE-{self.id}] Invalid transaction received')
      return False

    self.register_transaction(transaction)
    return True

  def verify_signature(self, transaction):
    signature = base64.b64decode(transaction['signature'])
    transaction_bytes = json.dumps({key: value for key, value in transaction.items() if key != 'signature'}).encode()
    public_key = serialization.load_pem_public_key(transaction['sender_address'].encode())

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
      print(f'[NODE-{self.id}] Invalid signature: {e}')
      return False

  def validate_transaction(self, transaction):
    required_keys = ['uuid', 'sender_address', 'receiver_address', 'timestamp', 'type_of_transaction', 'value', 'nonce', 'signature']
    if not all(key in transaction for key in required_keys):
      print(f'[NODE-{self.id}] Invalid transaction format')
      return False

    sender_key, receiver_key = transaction['sender_address'], transaction['receiver_address']
    sender = next((node for node in self.blockchain.nodes if node['key'] == sender_key), None)
    if not sender:
      print(f'[NODE-{self.id}] Invalid sender')
      return False

    receiver = 'stake_receiver' if receiver_key == '0' and transaction['type_of_transaction'] == 'stake' else next((node for node in self.blockchain.nodes if node['key'] == receiver_key), None)
    if not receiver:
      print(f'[NODE-{self.id}] Invalid receiver')
      return False

    if transaction['type_of_transaction'] not in ['coins', 'message', 'stake']:
      print(f'[NODE-{self.id}] Invalid transaction type')
      return False

    if transaction['nonce'] != sender['nonce']:
      print(f'[NODE-{self.id}] Invalid nonce')

      if sender['id'] == self.id:
        self.nonce = sender['nonce']

      return False

    if not self.verify_signature(transaction):
      print(f'[NODE-{self.id}] Invalid signature')
      return False

    available_balance = sender['balance'] - sender['stake']
    if transaction['type_of_transaction'] == 'coins':
      total_cost = (1 + self.blockchain.fee_rate) * transaction['value']
      if total_cost <= 0:
        print(f'[NODE-{self.id}] Invalid amount to transfer')
        return False
      if available_balance < total_cost:
        print(f'[NODE-{self.id}] Insufficient balance')
        print(f'[NODE-{self.id}] Available balance: {available_balance}, Total cost: {total_cost}')
        return False
    elif transaction['type_of_transaction'] == 'message':
      if not isinstance(transaction['value'], str):
        print(f'[NODE-{self.id}] Invalid message')
        return False
      if available_balance < len(transaction['value']):
        print(f'[NODE-{self.id}] Insufficient balance')
        return False
    elif transaction['type_of_transaction'] == 'stake':
      if transaction['value'] <= 0:
        print(f'[NODE-{self.id}] Invalid amount to stake')
        return False
      if transaction['value'] > available_balance:
        print(f'[NODE-{self.id}] Insufficient balance')
        return False

    return True

  def set_stake(self, amount):
    if amount <= 0.0 and amount > self.balance:
      print(f'[NODE-{self.id}] Insufficient balance or invalid amount to stake')
      return False

    self.execute_transaction(-1, 'stake', amount)

    return True

  def mine_block(self):
    validator_id = self.get_validator()

    if validator_id == self.id:
      transactions = sorted(self.current_block, key=lambda transaction: transaction.timestamp)
      new_block = Block(
        self.blockchain.block_index,
        self.id,
        transactions,
        self.blockchain.get_last_block().hash
      )

      self.broadcast_block(new_block)

  def get_validator(self):
    entries = []

    random.seed(self.blockchain.get_last_block().hash)

    for node in self.blockchain.nodes:
      entries.extend([node['id']] * int(node['stake']))

    if not entries:
      return 0

    return random.choice(entries)

  def broadcast_block(self, block):
    message = json.dumps({
      'message_type': 'block',
      'block': dict(block)
    })

    for node in self.blockchain.nodes:
      self.send(message, node['address'], node['port'])

  def receive_block(self, block):
    if len(self.current_block) < self.blockchain.block_capacity:
      print(f'[NODE-{self.id}] Received block while current block is not full')
      return False

    if not self.validate_block(block):
      print(f'[NODE-{self.id}] Invalid block received')
      return False

    self.register_block(block)

    return True

  def validate_block(self, block):
    required_keys = ['index', 'validator', 'transactions', 'previous_hash', 'timestamp', 'hash']
    if not all(key in block for key in required_keys):
      print(f'[NODE-{self.id}] Invalid block format')
      return False

    if block['validator'] != self.get_validator():
      print(f'[NODE-{self.id}] Invalid block validator')
      return False

    if block['previous_hash'] != self.blockchain.get_last_block().hash:
      print(f'[NODE-{self.id}] Invalid block previous hash')
      return False

    return True

  def register_block(self, block):
    self.blockchain.add_block(Block(**block))
    self.current_block = []

    validator = next((node for node in self.blockchain.nodes if node['id'] == block['validator']), None)
    validator['balance'] += self.current_fees
    self.current_fees = 0

    if validator['id'] == self.id:
      self.balance = validator['balance']

    print(f'[NODE-{self.id}] Block registered successfully')

class Bootstrap(Node):
  def __init__(self, blockchain):
    super().__init__()

    self.blockchain = blockchain
    self.id = 0

  def create_genesis_block(self, nodes_count):
    # Create the initial transaction
    transaction = Transaction(
      str(uuid.uuid4()),
      '0',
      self.wallet.get_address(),
      datetime.now().isoformat(),
      'coins',
      1000 * (nodes_count + 1),
      self.nonce,
      None
    )

    # Increment the nonce
    self.nonce += 1

    # Create the genesis block
    genesis_block = Block(0, 0, [transaction], '1')

    # Add the block to the blockchain
    self.blockchain.add_block(genesis_block)

    # Register the transaction
    self.balance += transaction.value

  def add_node(self, id, address, port, key, nonce=0, balance=0, stake=0):
    self.blockchain.nodes.append({
      'id': id,
      'address': address,
      'port': port,
      'key': key,
      'balance': balance,
      'stake': stake,
      'nonce': nonce
    })
