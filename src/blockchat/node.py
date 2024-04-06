"""A module for the Node class and the Bootstrap class.

This module contains the Node class and the Bootstrap class. The Node class
is used to represent a node in the blockchain network, while the Bootstrap
class is used to represent the bootstrap node.

The Node class is used to create a node in the blockchain network. It contains
methods for creating and validating transactions, as well as for mining blocks.

The Bootstrap class is used to create the bootstrap node in the blockchain
network. It contains methods for creating the genesis block, adding nodes to
the network, and broadcasting the blockchain to all nodes.
"""

import json
import base64
import random
import uuid
import re
import hashlib
import time
import os

from datetime import datetime
from threading import Thread, Lock
from queue import Queue
from socket import timeout

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization

from wallet import Wallet
from block import Block
from transaction import Transaction

from util import termcolor

class Node:
  """A class to represent a node in the blockchain network.

  Attributes:
    verbose (bool): A boolean indicating whether to increase output verbosity.
    debug (bool): A boolean indicating whether to enable debug mode.
    node_color (str): A string representing the color of the node.

    id (int): An integer representing the ID of the node.
    wallet (Wallet): A Wallet object representing the wallet of the node.
    balance (float): A float representing the balance of the node.
    nonce (int): An integer representing the nonce of the node.
    blockchain (Blockchain): A Blockchain object representing the blockchain of the network.
    stake (float): A float representing the stake of the node in the blockchain.

    current_block (list): A list of Transaction objects representing the current block of transactions not mined yet.
    current_fees (float): A float representing the current fees from completed transactions.

    past_fees (Queue): A Queue object representing the past fees of the blockchain.
    past_pools (Queue): A Queue object representing the past pools of validators of the blockchain.

  Methods:
    log: Log a message to the console.
    colorize: Colorize a message using the node color.
    send: Send a message to a specified address and port.
    set_stake: Set the stake of the node in the blockchain.
    execute_transaction: Execute a transaction.
    create_transaction: Create a transaction.
    sign_transaction: Sign a transaction using the node's private key.
    broadcast_transaction: Broadcast a transaction to all nodes in the blockchain network.
    receive_transaction: Receive a transaction from another node in the blockchain network.
    validate_transaction: Validate a transaction received from another node in the blockchain network.
    verify_signature: Verify the signature of a transaction using the sender's public key.
    register_transaction: Register a transaction in the blockchain.
    mine_block: Mine a block in the blockchain.
    get_validator_from_pool: Get the validator from a pool of validators.
    broadcast_block: Broadcast a block to all nodes in the blockchain network.
    receive_block: Receive a block from another node in the blockchain network.
    validate_block: Validate a block received from another node in the blockchain network.
    register_block: Register a block in the blockchain.
  """

  def __init__(self, bootstrap_address, bootstrap_port, verbose=True, debug=False, stake=0.0):
    """Initializes a new instance of Node.

    Args:
      verbose (bool): A boolean indicating whether to increase output verbosity.
      debug (bool): A boolean indicating whether to enable debug mode.
    """
    self.bootstrap_address = bootstrap_address
    self.bootstrap_port = bootstrap_port

    self.verbose = verbose
    self.debug = debug
    self.node_color = None
    self.node_counter = None

    self.id = None
    self.wallet = Wallet()
    self.nonce = 0
    self.blockchain = None
    self.stake = stake
    self.socket = None

    self.current_block = []
    self.current_fees = 0

    self.past_blocks = Queue()
    self.past_pools = Queue()

    self.transaction_queue = Queue()
    self.block_queue = Queue()

    self.balance_lock = Lock()
    self.blockchain_lock = Lock()

    self.test_messenger = Thread(target=self.transact_from_file)
    self.transaction_handler = Thread(target=self.handle_transactions)
    self.block_handler = Thread(target=self.handle_blocks)

    # Set threads as daemons
    self.test_messenger.daemon = True
    self.transaction_handler.daemon = True
    self.block_handler.daemon = True

    # Create a log file
    if not debug:
      self.log_file = f'logs-{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}.txt'
      open(self.log_file, 'w').close()

  def __del__(self):
    """Closes the socket connection and deletes the log file when the object is deleted."""

    print('Destructor called')

    if self.socket:
      self.socket.close()

    self.delete_logfile()

  def delete_logfile(self):
    """Deletes the log file."""

    try:
      os.remove(self.log_file)
    except FileNotFoundError:
      pass

  def log(self, message, is_log=False):
    """Log a message to the console setting a colored prefix for node identification.

    Args:
      message (str): The message.
    """

    if is_log:
      with open(self.log_file, 'a') as f:
        f.write(f'[{datetime.now().isoformat()}] {message}\n')

    elif self.verbose:
      if self.id == 0:
        print(f'{self.colorize("[BOOTSTRAP]")} {message}')
      elif self.id is None:
        print(f'{self.colorize("[NODE]")} {message}')
      else:
        print(f'{self.colorize(f"[NODE-{self.id}]")} {message}')

  def colorize(self, message):
    """Colorize a message based on node_color.

    Args:
      message (str): The message.
    """

    if self.node_color is None:
      return message
    return self.node_color + termcolor.bold(message) + termcolor.RESET_COLOR

  def send(self, message, address, port):
    """Send a message to a specified address and port using UDP.

    Args:
      message (str): The message.
      address (str): The address.
      port (int): The port.
    """

    self.socket.sendto(message.encode(), (address, port))

  def ping_bootstrap(self):
    """Pings bootstrap node to check if it is online, until it responds.

    Args:
      address (str): The address of the node.
      port (int): The port of the node.
    """
    self.socket.settimeout(0.1)
    while True:
      try:
        self.log(termcolor.magenta('Pinging bootstrap node...'))
        self.send(json.dumps({'message_type': 'ping'}), self.bootstrap_address, self.bootstrap_port)
        message, (address, port) = self.socket.recvfrom(1024)

        if message == b'pong' and address == self.bootstrap_address and port == self.bootstrap_port:
          break

      except timeout:
        self.log(termcolor.yellow('Bootstrap node is not available. Retrying...'))
    self.log(termcolor.green('Bootstrap node is available'))
    self.socket.settimeout(None)

  def send_key(self):
    """Sends the public key of the node to the bootstrap node."""

    message = json.dumps({
      'message_type': 'key',
      'key': self.wallet.get_address(),
      'stake': self.stake
    })

    self.log(termcolor.magenta('Sending key to bootstrap node'))
    self.send(message, self.bootstrap_address, self.bootstrap_port)

  def add_node(self, id, key, address, port, stake=0, nonce=0, balance=0):
    """Adds a node to the blockchain network.

    Args:
      id (int): The ID of the node.
      address (str): The address of the node.
      port (int): The port of the node.
      key (str): The public key of the node.
      nonce (int): The nonce of the node.
      balance (float): The balance of the node.
      stake (float): The stake of the node.
    """

    new_node = {
      'id': id,
      'address': address,
      'port': port,
      'key': key,
      'stake': stake,
      'balance': balance,
      'nonce': nonce
    }
    self.blockchain.nodes.append(new_node)
    self.node_counter += 1
    self.log(termcolor.blue(f'Added node {new_node["id"]}'), not self.debug)

    return new_node

  def set_stake(self, amount):
    """Set the stake of the node in the blockchain.

    Args:
      amount (float): The amount to stake.
    """

    self.log(termcolor.magenta(f'Setting stake to {amount}'))

    self.execute_transaction(-1, 'stake', amount)

  def transact_from_file(self):
    """Execute transactions from a file.

    This method reads a file containing transactions and executes them.

    Args:
      file_path (str): The path to the file containing transactions.
    """

    pattern = re.compile(r'id(\d+)\s+(.*)')
    file_path = f'input/trans{self.id}.txt'

    try:
      with open(file_path, 'r') as f:
        for line in f:
          time.sleep(random.uniform(0.1, 0.5))  #! simulate user input delay (fast), comment out for benchmarking
          match = pattern.match(line)
          if match:
            receiver_id = int(match.group(1))
            message = match.group(2)

            if receiver_id < len(self.blockchain.nodes):
              self.execute_transaction(receiver_id, 'message', message)
    except FileNotFoundError:
      self.log(termcolor.red(f'File not found: {file_path}'))
    except IOError:
      self.log(termcolor.red(f'Error reading file: {file_path}'))

  def execute_transaction(self, receiver_id, type_of_transaction, value):
    """Executes a transaction.

    This method checks if the transaction is valid and if the sender has
    enough balance to execute the transaction. If the transaction is valid,
    it creates a transaction object using the create_transaction method and
    broadcasts the transaction to all nodes in the blockchain network using
    the broadcast_transaction method.

    Args:
      receiver_id (int): The ID of the receiver.
      type_of_transaction (str): The type of transaction.
      value (float): The value of the transaction.

    Returns:
      bool: True if the transaction was executed successfully, False otherwise.
    """

    # Get the receiver and check if it exists
    receiver = next((node for node in self.blockchain.nodes if node['id'] == receiver_id), None) if receiver_id != -1 else {'key': '0'}
    if not receiver:
      self.log(termcolor.red(f'Execute: Invalid receiver: {receiver_id}'))
      return False

    # Check if the transaction is valid and if the sender has enough balance
    with self.balance_lock:
      available_balance = self.wallet.balance - self.stake
      if type_of_transaction == 'stake':
        if value <= 0.0:
          self.log(termcolor.red(f'Execute: Invalid amount to stake: {value}'))
          return False
        elif value > self.wallet.balance:
          self.log(termcolor.red(f'Execute: Insufficient balance to stake: {self.wallet.balance} < {float(value)} (stake)'))
          return False
        else:
          self.stake = value
      elif type_of_transaction == 'coins':
        total_cost = (1.0 + self.blockchain.fee_rate) * value
        if total_cost <= 0.0:
          self.log(termcolor.red(f'Execute: Invalid amount to transfer: {value}'))
          return False
        elif available_balance < total_cost:
          self.log(termcolor.red(f'Execute: Insufficient balance to transfer: {available_balance} < {total_cost} (transfer)'))
          return False
        else:
          self.wallet.balance -= total_cost
      elif type_of_transaction == 'message':
        if not isinstance(value, str):
          self.log(termcolor.red('Execute: Invalid message to send'))
          return False
        elif available_balance < len(value):
          self.log(termcolor.red(f'Execute: Insufficient balance to send message: {available_balance} < {float(len(value))} (message)'))
          return False
        else:
          self.wallet.balance -= len(value)
      else:
        self.log(termcolor.red(f'Execute: Invalid transaction type: {type_of_transaction}'))
        return False

    # Sign and get the transaction object
    transaction = self.create_transaction(receiver['key'], type_of_transaction, value)

    self.log(termcolor.magenta(f'Executing transaction {termcolor.underline(transaction.uuid)}'))

    self.broadcast_transaction(transaction)

    return True

  def create_transaction(self, receiver_address, type_of_transaction, value):
    """Creates a transaction object based on the given parameters.

    Args:
      receiver_address (str): The address of the receiver.
      type_of_transaction (str): The type of the transaction, one of 'coins', 'message', or 'stake'.
      value (float): The value of the transaction.

    Returns:
      Transaction: The transaction.
    """

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
    """Signs a transaction using the node's private key.

    This method uses methods from the 'crypto' module to sign the transaction.

    Args:
      transaction (dict): The transaction.

    Returns:
      str: The signature of the transaction.
    """

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
    """Broadcasts a transaction to all nodes in the blockchain network.

    Args:
      transaction (Transaction): The transaction.
    """

    message = json.dumps({
      'message_type': 'transaction',
      'transaction': dict(transaction)
    })

    self.log(termcolor.magenta(f'Broadcasting transaction {termcolor.underline(transaction.uuid)}'))
    for node in self.blockchain.nodes:
      self.send(message, node['address'], node['port'])

  def receive_transaction(self, transaction):
    """Handles a transaction received from another node in the blockchain network.

    This method first validates the transaction using the validate_transaction
    method. If the transaction is valid, it registers the transaction using the
    register_transaction method.

    Args:
      transaction (dict): The transaction.

    Returns:
      bool: True if the transaction was received and handled successfully, False otherwise.
    """

    self.log(termcolor.blue(f'Received transaction {termcolor.underline(transaction["uuid"])}'), not self.debug)
    self.transaction_queue.put(transaction)

  def handle_transactions(self):
    """Handles transactions from the transaction queue."""

    while True:
      transaction = self.transaction_queue.get()
      if not self.validate_transaction(transaction):
        self.log(termcolor.yellow(f'Transaction {termcolor.underline(transaction["uuid"])} is invalid'), not self.debug)
        continue

      self.register_transaction(transaction)

  def validate_transaction(self, transaction):
    """Validates a transaction

    This method checks if the transaction is valid based on the following
    criteria:
      - The transaction has all the required keys.
      - The sender and receiver addresses are valid.
      - The type of the transaction is valid.
      - The nonce of the sender is valid.
      - The signature of the transaction is valid.
      - The sender has enough balance to execute the transaction.

    Args:
      transaction (dict): The transaction.

    Returns:
      bool: True if the transaction is valid, False otherwise.
    """

    self.log(termcolor.magenta(f'Validating transaction {termcolor.underline(transaction["uuid"])}'), not self.debug)

    # Check if the transaction has all the required keys
    required_keys = ['uuid', 'sender_address', 'receiver_address', 'timestamp', 'type_of_transaction', 'value', 'nonce', 'signature']
    if not all(key in transaction for key in required_keys):
      self.log(termcolor.red(f'Validate transaction {termcolor.underline(transaction["uuid"])}: Invalid transaction format'), not self.debug)
      return False

    # Check if the sender and receiver addresses are valid
    sender_key, receiver_key = transaction['sender_address'], transaction['receiver_address']
    sender = next((node for node in self.blockchain.nodes if node['key'] == sender_key), None)
    if not sender:
      self.log(termcolor.red(f'Validate transaction {termcolor.underline(transaction["uuid"])}: Invalid sender: {sender_key}'), not self.debug)
      return False
    else:
      with self.blockchain_lock:
        sender['nonce'] += 1

    receiver = 'stake_receiver' if receiver_key == '0' and transaction['type_of_transaction'] == 'stake' else next((node for node in self.blockchain.nodes if node['key'] == receiver_key), None)
    if not receiver:
      self.log(termcolor.red(f'Validate transaction {termcolor.underline(transaction["uuid"])}: Invalid receiver: {receiver_key}'), not self.debug)
      return False

    # Check if the type of the transaction is valid
    if transaction['type_of_transaction'] not in ['coins', 'message', 'stake']:
      self.log(termcolor.red(f'Validate transaction {termcolor.underline(transaction["uuid"])}: Invalid transaction type: {transaction["type_of_transaction"]}'), not self.debug)
      return False

    # Check if the nonce of the sender is valid
    if transaction['nonce'] != sender['nonce'] - 1:
      self.log(termcolor.red(f'Validate transaction {termcolor.underline(transaction["uuid"])}: Invalid nonce: {transaction["nonce"]} != {sender["nonce"] - 1} (expected)'), not self.debug)
      return False

    # Check if the signature of the transaction is valid
    if not self.verify_signature(transaction):
      self.log(termcolor.red(f'Validate transaction {termcolor.underline(transaction["uuid"])}: Signature verification failed'), not self.debug)
      return False

    # Check if the hash of the transaction is the expected one
    expected_hash = hashlib.sha256(json.dumps({key: value for key, value in transaction.items() if key != 'hash'}).encode()).hexdigest()
    if transaction['hash'] != expected_hash:
      self.log(termcolor.red(f'Validate transaction {termcolor.underline(transaction["uuid"])}: Invalid hash: {transaction["hash"]} != {expected_hash} (expected)'), not self.debug)
      return False

    # Check if the sender has enough balance to execute the transaction
    available_balance = sender['balance'] - sender['stake']
    if transaction['type_of_transaction'] == 'coins':
      total_cost = (1.0 + self.blockchain.fee_rate) * transaction['value']
      if total_cost <= 0:
        self.log(termcolor.red(f'Validate transaction {termcolor.underline(transaction["uuid"])}: Invalid amount to transfer: {transaction["value"]}'), not self.debug)
        return False
      if available_balance < total_cost:
        self.log(termcolor.red(f'Validate transaction {termcolor.underline(transaction["uuid"])}: Insufficient balance: {available_balance} < {total_cost}'), not self.debug)
        return False
    elif transaction['type_of_transaction'] == 'message':
      if not isinstance(transaction['value'], str):
        self.log(termcolor.red(f'Validate transaction {termcolor.underline(transaction["uuid"])}: Invalid message'))
        return False
      if available_balance < len(transaction['value']):
        self.log(termcolor.red(f'Validate transaction {termcolor.underline(transaction["uuid"])}: Insufficient balance: {available_balance} < {float(len(transaction["value"]))}')), not self.debug
        return False
    elif transaction['type_of_transaction'] == 'stake':
      if transaction['value'] <= 0:
        self.log(termcolor.red(f'Validate transaction {termcolor.underline(transaction["uuid"])}: Invalid amount to stake: {transaction["value"]}'))
        return False
      if transaction['value'] > sender['balance']:
        self.log(termcolor.red(f'Validate transaction {termcolor.underline(transaction["uuid"])}: Insufficient balance: {sender["balance"]} < {transaction["value"]}'), not self.debug)
        return False

    self.log(termcolor.green(f'Transaction {termcolor.underline(transaction["uuid"])} validated successfully'), not self.debug)
    return True

  def verify_signature(self, transaction):
    """Verifies the signature of a transaction using the sender's public key.

    This method uses methods from the 'crypto' module to verify the signature.

    Args:
      transaction (dict): The transaction.

    Returns:
      bool: True if the signature is valid, False otherwise.
    """

    signature = base64.b64decode(transaction['signature'])
    transaction_bytes = json.dumps({key: value for key, value in transaction.items() if key != 'signature' and key != 'hash'}).encode()
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
      self.log(termcolor.red(f'Verify transaction {termcolor.underline(transaction["uuid"])}: Signature verification failed'), not self.debug)
      return False

  def register_transaction(self, transaction):
    """Registers a transaction in the blockchain and updates info accordingly.

    Args:
      transaction (dict): The transaction.
    """

    self.log(termcolor.magenta(f'Registering transaction {termcolor.underline(transaction["uuid"])}'), not self.debug)

    sender = next((node for node in self.blockchain.nodes if node['key'] == transaction['sender_address']), None)
    receiver = next((node for node in self.blockchain.nodes if node['key'] == transaction['receiver_address']), None)

    # Update balances and stakes
    with self.blockchain_lock:
      if transaction['type_of_transaction'] == 'coins':
        total_cost = (1.0 + self.blockchain.fee_rate) * transaction['value']
        sender['balance'] -= total_cost
        receiver['balance'] += transaction['value']
        self.current_fees += total_cost - transaction['value']

        with self.balance_lock:
          if receiver['id'] == self.id:
            self.wallet.balance += transaction['value']

      elif transaction['type_of_transaction'] == 'message':
        sender['balance'] -= len(transaction['value'])
        self.current_fees += len(transaction['value'])

      elif transaction['type_of_transaction'] == 'stake':
        sender['stake'] = transaction['value']

    self.log(termcolor.green(f'Transaction {termcolor.underline(transaction["uuid"])} registered successfully: {sender["id"]} -> {receiver["id"] if receiver is not None else "none"}, {transaction["type_of_transaction"]}: {transaction["value"]}'), not self.debug)

    # Add the transaction to the current block and mine if the block is full
    self.current_block.append(Transaction(**transaction))
    if len(self.current_block) == self.blockchain.block_capacity:
      self.past_blocks.put(self.current_block)
      current_block_copy = self.current_block.copy()
      self.current_block = []

      self.log(termcolor.blue('Reached block capacity. Starting mining process'), not self.debug)
      self.mine_block(current_block_copy)

  def mine_block(self, current_block):
    """Mines a block in the blockchain.

    This method first creates a list of validators based on the stake of each
    node in the blockchain. It then uses the get_validator_from_pool method to
    pick a validator from the list of validators. If the node is picked as the
    validator, it creates a new block using the current block of transactions
    and broadcasts the block to all nodes in the blockchain network using the
    broadcast_block method.

    """

    # Create a list of validators based on the stake of each node
    entries = []
    for node in self.blockchain.nodes:
      entries.extend([node['id']] * int(node['stake']))

    seed = self.blockchain.get_last_block().hash

    validator_id = self.get_validator_from_pool(entries, seed)
    self.log(termcolor.blue(f'Node {validator_id} was picked as the validator for block {self.blockchain.block_index}'), not self.debug)

    # Save the current fees and transactions for easier block validation and registration
    self.past_pools.put(entries)

    if validator_id == self.id:
      self.log(termcolor.magenta('Mining block'), not self.debug)

      transactions = sorted(current_block, key=lambda transaction: transaction.timestamp)
      new_block = Block(
        self.blockchain.block_index,
        self.id,
        transactions,
        self.blockchain.get_last_block().hash
      )

      with self.balance_lock:
        self.wallet.balance += self.current_fees

      self.broadcast_block(new_block)

    self.current_fees = 0

    while not self.past_blocks.empty():
      pass

  @staticmethod
  def get_validator_from_pool(pool, seed):
    """Picks a validator from a pool of validators based on a specified seed.

    Args:
      pool (list): A list of validators.
      seed (str): The seed.

    Returns:
      int: The ID of the validator.
    """

    random.seed(seed)

    if not pool:
      return 0

    return random.choice(pool)

  def broadcast_block(self, block):
    """Broadcasts a block to all nodes in the blockchain network.

    Args:
      block (Block): The block.
    """

    message = json.dumps({
      'message_type': 'block',
      'block': dict(block)
    })

    self.log(termcolor.magenta(f'Broadcasting new block: {block.index}'), not self.debug)
    for node in self.blockchain.nodes:
      self.send(message, node['address'], node['port'])

  def receive_block(self, block):
    """Handles a block received from another node in the blockchain network.

    This method first validates the block using the validate_block method. If
    the block is valid, it registers the block using the register_block method.

    Args:
      block (dict): The block.

    Returns:
      bool: True if the block was received and handled successfully, False otherwise.
    """

    self.log(termcolor.blue(f'Received block {block["index"]}'), not self.debug)
    self.block_queue.put(block)

  def handle_blocks(self):
    """Handles blocks from the block queue."""

    while True:
      block = self.block_queue.get()
      if not self.validate_block(block):
        self.log(termcolor.yellow(f'Block {block["index"]} is invalid'), not self.debug)
        continue

      self.register_block(block)

  def validate_block(self, block):
    """Validates a block.

    This method checks if the block is valid based on the following criteria:
      - The block has all the required keys.
      - The previous hash of the block is valid.
      - The validator of the block is valid.

    Args:
      block (dict): The block.

    Returns:
      bool: True if the block is valid, False otherwise.
    """

    self.log(termcolor.magenta(f'Validating block {block["index"]}'), not self.debug)

    # Check if the block has all the required keys
    required_keys = ['index', 'validator', 'transactions', 'previous_hash', 'timestamp', 'hash']
    if not all(key in block for key in required_keys):
      self.log(termcolor.red(f'Validate block {block["index"]}: Invalid block format'), not self.debug)
      return False

    # Check if the previous hash of the block is valid
    if block['previous_hash'] != self.blockchain.get_last_block().hash:
      self.log(termcolor.red(f'Validate block {block["index"]}: Invalid previous hash'), not self.debug)
      return False

    # Check if the validator of the block is valid
    expected_validator = self.get_validator_from_pool(self.past_pools.get(), block['previous_hash'])
    if block['validator'] != expected_validator:
      self.log(termcolor.red(f'Validate block {block["index"]}: Invalid validator'), not self.debug)
      return False

    # Check if the block has the expected hash
    expected_hash = hashlib.sha256(json.dumps({
      'index': self.blockchain.block_index,
      'timestamp': block['timestamp'],
      'validator': expected_validator,
      'transactions': [dict(transaction) for transaction in block['transactions']],
      'previous_hash': self.blockchain.get_last_block().hash,
    }).encode()).hexdigest()
    if block['hash'] != expected_hash:
      self.log(termcolor.red(f'Validate block {block["index"]}: Invalid hash'), not self.debug)
      return False

    self.log(termcolor.green(f'Block {block["index"]} validated successfully'), not self.debug)
    return True

  def register_block(self, block):
    """Registers a block in the blockchain and updates info accordingly.

    Args:
      block (dict): The block.
    """

    self.log(termcolor.magenta(f'Registering block {block["index"]}'), not self.debug)

    with self.blockchain_lock:
      self.blockchain.add_block(Block(**block))
      self.nodes, credit = self.blockchain.get_state()

      validator = next((node for node in self.blockchain.nodes if node['id'] == block['validator']), None)
      validator['balance'] += credit
      self.log(termcolor.green(f'Node {block["validator"]} credited with {credit} BCC for mining block {block["index"]}'), not self.debug)

    self.past_blocks.get()

    self.log(termcolor.green(f'Block {block["index"]} registered successfully'), not self.debug)

  def validate_chain(self, blockchain):
    """Validates the blockchain.

    This method validates the blockchain by checking if the blocks are valid
    and if the transactions are valid.

    Returns:
      bool: True if the blockchain is valid, False otherwise.
    """

    self.log(termcolor.magenta('Validating blockchain'))

    for i in range(1, len(blockchain.chain)):
      previous_block = blockchain.chain[i-1]
      current_block = blockchain.chain[i]

      # Check if the index of the block is valid
      if current_block.index != i:
        self.log(termcolor.red(f'Block {i} is invalid: Invalid index {current_block.index}'))
        return False

      # Check if the previous hash of the block is valid
      if current_block.previous_hash != previous_block.hash:
        self.log(termcolor.red(f'Block {current_block.index} is invalid: Invalid previous hash'))
        return False

      # Check if the block has the expected hash
      expected_hash = hashlib.sha256(json.dumps({
        'index': current_block.index,
        'timestamp': current_block.timestamp,
        'validator': current_block.validator,
        'transactions': [dict(transaction) for transaction in current_block.transactions],
        'previous_hash': current_block.previous_hash,
      }).encode()).hexdigest()
      if current_block.hash != expected_hash:
        self.log(termcolor.red(f'Block {current_block.index} is invalid: Invalid hash'))
        return False

    self.log(termcolor.green('Blockchain is valid'))
    return True

class Bootstrap(Node):
  def __init__(self, bootstrap_address, bootstrap_port, verbose, debug, blockchain=None, stake=0.0):
    super().__init__(bootstrap_address, bootstrap_port, verbose, debug, stake)

    self.blockchain = blockchain
    self.id = 0
    self.node_counter = 0

  def create_genesis_block(self, nodes_count):
    """Creates the genesis block and adds it to the blockchain.

    This method also credits the bootstrap node with an amount based on the
    number of nodes in the blockchain network.

    Args:
      nodes_count (int): The number of nodes in the blockchain network.
    """

    transaction = Transaction(
      str(uuid.uuid4()),
      '0',
      self.wallet.get_address(),
      datetime.now().isoformat(),
      'coins',
      1000 * nodes_count,
      0,
      None
    )

    genesis_block = Block(0, 0, [transaction], '1')

    self.blockchain.add_block(genesis_block)

    self.wallet.balance += transaction.value

    self.log(termcolor.blue('Genesis block created'))

  def broadcast_node(self, new_node):
    """Broadcasts a newly added node to all nodes in the blockchain network.

    Args:
      id (int): The ID of the node.
      address (str): The address of the node.
      port (int): The port of the node.
      key (str): The public key of the node.
    """

    message = json.dumps({
      'message_type': 'node',
      'node': new_node
    })

    self.log(termcolor.magenta(f'Broadcasting new node: {new_node["id"]}'), not self.debug)
    for node in self.blockchain.nodes:
      if node['id'] != new_node['id'] and node['id'] != 0:
        self.send(message, node['address'], node['port'])

  def activate_node(self, node, color):
    """Activates a node in the blockchain network.

    Args:
      node (dict): The node.
    """

    message = json.dumps({
      'message_type': 'activate',
      'id': node['id'],
      'color': color,
      'blockchain': dict(self.blockchain),
      'current_block': [dict(transaction) for transaction in self.current_block],
    })

    self.log(termcolor.magenta(f'Activating node: {node["id"]}'), not self.debug)
    self.send(message, node['address'], node['port'])
