import json
import socket
import base64
import random
import uuid
from datetime import datetime
from queue import Queue
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization

from wallet import Wallet
from block import Block
from transaction import Transaction

from util import termcolor

class Node:
  def __init__(self, verbose, debug):
    self.verbose = verbose
    self.debug = debug
    self.node_color = None

    self.id = None
    self.wallet = Wallet()
    self.balance = 0.0
    self.nonce = 0
    self.blockchain = None
    self.stake = 0
    self.socket = None

    self.current_block = []
    self.current_fees = 0

    self.past_fees = Queue()
    self.past_pools = Queue()

  def log(self, message):
    if self.verbose:
      if self.id is None or self.debug or self.id <= 0:
        if self.id == 0:
          print(f'{self.colorize("[BOOTSTRAP]")} {message}')
        elif self.id is None:
          print(f'{self.colorize("[NODE]")} {message}')
        else:
          print(f'{self.colorize(f"[NODE-{self.id}]")} {message}')

  def colorize(self, message):
    if self.node_color is None:
      return message
    return self.node_color + termcolor.bold(message) + termcolor.RESET_COLOR

  @staticmethod
  def send(message, address, port):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
      s.sendto(message.encode(), (address, port))

  def set_stake(self, amount):
    self.log(termcolor.magenta(f'Setting stake to {amount}'))

    self.execute_transaction(-1, 'stake', amount)

    return True

  def execute_transaction(self, receiver_id, type_of_transaction, value):
    receiver = next((node for node in self.blockchain.nodes if node['id'] == receiver_id), None) if receiver_id != -1 else {'key': '0'}
    if not receiver:
      self.log(termcolor.red(f'Execute: Invalid receiver: {receiver_id}'))
      return False

    available_balance = self.balance - self.stake
    if type_of_transaction == 'stake':
      if value <= 0.0:
        self.log(termcolor.red(f'Execute: Invalid amount to stake: {value}'))
        return False
      if value > available_balance:
        self.log(termcolor.red(f'Execute: Insufficient balance to stake: {value} > {available_balance}'))
        return False
    elif type_of_transaction == 'coins':
      total_cost = (1 + self.blockchain.fee_rate) * value
      if total_cost <= 0.0:
        self.log(termcolor.red(f'Execute: Invalid amount to transfer: {value}'))
        return False
      if available_balance < total_cost:
        self.log(termcolor.red(f'Execute: Insufficient balance to transfer: {total_cost} > {available_balance}'))
        return False
    elif type_of_transaction == 'message':
      if not isinstance(value, str):
        self.log(termcolor.red('Execute: Invalid message to send'))
        return False
      if available_balance < len(value):
        self.log(termcolor.red(f'Execute: Insufficient balance to send message: {len(value)} > {available_balance}'))
        return False
    else:
      self.log(termcolor.red(f'Execute: Invalid transaction type: {type_of_transaction}'))
      return False

    transaction = self.create_transaction(receiver['key'], type_of_transaction, value)

    self.log(termcolor.magenta(f'Executing transaction {termcolor.underline(transaction.uuid)}'))

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

    sender_id = next((node['id'] for node in self.blockchain.nodes if node['key'] == transaction['sender_address']), None)
    receiver_id = next((node['id'] for node in self.blockchain.nodes if node['key'] == transaction['receiver_address']), None)
    self.log(termcolor.magenta(f'Creating Transaction: {termcolor.underline(transaction["uuid"])}: {sender_id} -> {receiver_id}, {transaction["type_of_transaction"]}: {transaction["value"]}'))

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

  def broadcast_transaction(self, transaction):
    message = json.dumps({
      'message_type': 'transaction',
      'transaction': dict(transaction)
    })

    self.log(termcolor.magenta(f'Broadcasting transaction {termcolor.underline(transaction.uuid)}'))

    for node in self.blockchain.nodes:
      self.send(message, node['address'], node['port'])

  def receive_transaction(self, transaction):
    self.log(termcolor.blue(f'Received transaction {termcolor.underline(transaction["uuid"])}'))

    if not self.validate_transaction(transaction):
      self.log(termcolor.yellow(f'Transaction {termcolor.underline(transaction["uuid"])} is invalid'))
      return False

    self.register_transaction(transaction)
    return True

  def validate_transaction(self, transaction):
    self.log(termcolor.magenta(f'Validating transaction {termcolor.underline(transaction["uuid"])}'))

    required_keys = ['uuid', 'sender_address', 'receiver_address', 'timestamp', 'type_of_transaction', 'value', 'nonce', 'signature']
    if not all(key in transaction for key in required_keys):
      self.log(termcolor.red(f'Validate transaction {termcolor.underline(transaction["uuid"])}: Invalid transaction format'))
      return False

    sender_key, receiver_key = transaction['sender_address'], transaction['receiver_address']
    sender = next((node for node in self.blockchain.nodes if node['key'] == sender_key), None)
    if not sender:
      self.log(termcolor.red(f'Validate transaction {termcolor.underline(transaction["uuid"])}: Invalid sender: {sender_key}'))
      return False

    receiver = 'stake_receiver' if receiver_key == '0' and transaction['type_of_transaction'] == 'stake' else next((node for node in self.blockchain.nodes if node['key'] == receiver_key), None)
    if not receiver:
      self.log(termcolor.red(f'Validate transaction {termcolor.underline(transaction["uuid"])}: Invalid receiver: {receiver_key}'))
      return False

    if transaction['type_of_transaction'] not in ['coins', 'message', 'stake']:
      self.log(termcolor.red(f'Validate transaction {termcolor.underline(transaction["uuid"])}: Invalid transaction type: {transaction["type_of_transaction"]}'))
      return False

    if transaction['nonce'] != sender['nonce']:
      self.log(termcolor.red(f'Validate transaction {termcolor.underline(transaction["uuid"])}: Invalid nonce: {transaction["nonce"]} (expected) != {sender["nonce"]}'))

      if sender['id'] == self.id:
        self.nonce = sender['nonce']

      return False

    if not self.verify_signature(transaction):
      self.log(termcolor.red(f'Validate transaction {termcolor.underline(transaction["uuid"])}: Signature verification failed'))
      return False

    available_balance = sender['balance'] - sender['stake']
    if transaction['type_of_transaction'] == 'coins':
      total_cost = (1 + self.blockchain.fee_rate) * transaction['value']
      if total_cost <= 0:
        self.log(termcolor.red(f'Validate transaction {termcolor.underline(transaction["uuid"])}: Invalid amount to transfer: {transaction["value"]}'))
        return False
      if available_balance < total_cost:
        self.log(termcolor.red(f'Validate transaction {termcolor.underline(transaction["uuid"])}: Insufficient balance: {available_balance} < {total_cost}'))
        return False
    elif transaction['type_of_transaction'] == 'message':
      if not isinstance(transaction['value'], str):
        self.log(termcolor.red(f'Validate transaction {termcolor.underline(transaction["uuid"])}: Invalid message'))
        return False
      if available_balance < len(transaction['value']):
        self.log(termcolor.red(f'Validate transaction {termcolor.underline(transaction["uuid"])}: Insufficient balance: {available_balance} < {len(transaction["value"])}'))
        return False
    elif transaction['type_of_transaction'] == 'stake':
      if transaction['value'] <= 0:
        self.log(termcolor.red(f'Validate transaction {termcolor.underline(transaction["uuid"])}: Invalid amount to stake: {transaction["value"]}'))
        return False
      if transaction['value'] > available_balance:
        self.log(termcolor.red(f'Validate transaction {termcolor.underline(transaction["uuid"])}: Insufficient balance: {available_balance} < {transaction["value"]}'))
        return False

    self.log(termcolor.green(f'Transaction {termcolor.underline(transaction["uuid"])} validated successfully'))
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
    except Exception:
      self.log(termcolor.red(f'Verify transaction {termcolor.underline(transaction["uuid"])}: Signature verification failed'))
      return False

  def register_transaction(self, transaction):
    self.log(termcolor.magenta(f'Registering transaction {termcolor.underline(transaction["uuid"])}'))

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

    self.log(termcolor.green(f'Transaction {termcolor.underline(transaction["uuid"])} registered successfully: {sender["id"]} -> {receiver["id"] if receiver is not None else "none"}, {transaction["type_of_transaction"]}: {transaction["value"]}'))

    self.current_block.append(Transaction(**transaction))
    if len(self.current_block) == self.blockchain.block_capacity:
      self.log(termcolor.blue('Reached transaction limit. Starting mining process'))
      self.mine_block()

  def mine_block(self):
    entries = []
    for node in self.blockchain.nodes:
      entries.extend([node['id']] * int(node['stake']))

    seed = self.blockchain.get_last_block().hash

    validator_id = self.get_validator_from_pool(entries, seed)
    self.log(termcolor.blue(f'Node {validator_id} was picked as the validator for block {self.blockchain.block_index}'))

    self.past_fees.put(self.current_fees)
    self.past_pools.put(entries)

    if validator_id == self.id:
      self.log(termcolor.magenta('Mining block'))
      transactions = sorted(self.current_block, key=lambda transaction: transaction.timestamp)
      new_block = Block(
        self.blockchain.block_index,
        self.id,
        transactions,
        self.blockchain.get_last_block().hash
      )

      self.broadcast_block(new_block)

    self.current_fees = 0

  @staticmethod
  def get_validator_from_pool(pool, seed):
    random.seed(seed)

    if not pool:
      return 0

    return random.choice(pool)

  def broadcast_block(self, block):
    message = json.dumps({
      'message_type': 'block',
      'block': dict(block)
    })

    self.log(termcolor.magenta(f'Broadcasting new block: {block.index}'))
    for node in self.blockchain.nodes:
      self.send(message, node['address'], node['port'])

  def receive_block(self, block):
    self.log(termcolor.blue(f'Received block {block["index"]}'))

    if len(self.current_block) < self.blockchain.block_capacity:
      self.log(termcolor.yellow('Received block while current block is not full'))
      return False

    if not self.validate_block(block):
      self.log(termcolor.yellow(f'Block {block["index"]} is invalid'))
      return False

    self.register_block(block)

    return True

  def validate_block(self, block):
    self.log(termcolor.magenta(f'Validating block {block["index"]}'))

    required_keys = ['index', 'validator', 'transactions', 'previous_hash', 'timestamp', 'hash']
    if not all(key in block for key in required_keys):
      self.log(termcolor.red(f'Validate block {block["index"]}: Invalid block format'))
      return False

    if block['previous_hash'] != self.blockchain.get_last_block().hash:
      self.log(termcolor.red(f'Validate block {block["index"]}: Invalid previous hash'))
      return False

    pool = self.past_pools.get()
    if block['validator'] != self.get_validator_from_pool(pool, block['previous_hash']):
      self.log(termcolor.red(f'Validate block {block["index"]}: Invalid validator'))
      return False

    self.log(termcolor.green(f'Block {block["index"]} validated successfully'))
    return True

  def register_block(self, block):
    self.log(termcolor.magenta(f'Registering block {block["index"]}'))

    self.blockchain.add_block(Block(**block))
    self.current_block = self.current_block[self.blockchain.block_capacity:]

    validator = next((node for node in self.blockchain.nodes if node['id'] == block['validator']), None)
    validator['balance'] += self.past_fees.get()

    if validator['id'] == self.id:
      self.balance = validator['balance']

    self.log(termcolor.green(f'Block {block["index"]} registered successfully'))

class Bootstrap(Node):
  def __init__(self, verbose, debug, blockchain):
    super().__init__(verbose, debug)

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

    self.log(termcolor.blue('Genesis block created'))

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

    self.log(termcolor.blue(f'Added node {id}'))
