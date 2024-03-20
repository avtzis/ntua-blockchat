"""A module for the Bootstrap process.

This module contains the start_bootstrap function, which is used to start the
bootstrap process of the network.
"""

import socket
import json
import itertools

from node import Bootstrap
from blockchain import Blockchain

from util import termcolor

def start_bootstrap(nodes_count, block_capacity, bootstrap_address, bootstrap_port, verbose, debug):
  """Starts the bootstrap process of the network.

  This function starts the bootstrap process of the network, which is used to
  initialize the blockchain and the nodes. It creates the blockchain, the
  bootstrap node, the genesis block, and waits for the nodes to connect.

  Args:
    nodes_count (int): The number of nodes in the network.
    block_capacity (int): The capacity of each block in the blockchain.
    bootstrap_address (str): The address of the bootstrap node.
    bootstrap_port (int): The port of the bootstrap node.
    verbose (bool): Whether to enable verbose mode.
    debug (bool): Whether to enable debug mode.
  """

  blockchain = Blockchain(block_capacity)
  print(termcolor.red('[BOOTSTRAP]'), termcolor.blue('Blockchain created'))

  bootstrap = Bootstrap(verbose, debug, blockchain, stake=10.0)

  colors = termcolor.colors
  bootstrap.node_color = colors.pop(0)
  color = itertools.cycle(colors)

  bootstrap.create_genesis_block(nodes_count)

  # Start the UDP server
  with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.bind((bootstrap_address, bootstrap_port))
    address, port = s.getsockname()
    bootstrap.log(termcolor.blue(f'Listening on {termcolor.underline(f"{address}:{port}")}'))

    # Wait for the nodes to connect
    addresses = []
    for i in range(nodes_count):
      while True:
        message, (address, port) = s.recvfrom(1024)
        if message == b'ping' and (address, port) not in addresses:
          s.sendto(b'pong', (address, port))
          addresses.append((address, port))
          bootstrap.log(termcolor.blue(f'Connected: {addresses}'))
          break

    for address in addresses:
      s.sendto(b'ready', address)

    bootstrap.add_node(0, bootstrap_address, bootstrap_port, bootstrap.wallet.get_address(), bootstrap.nonce, bootstrap.balance)

    # Wait for the nodes to send their public keys
    node_id = 0
    while len(blockchain.nodes) - 1 < nodes_count:
      node_id += 1
      message, (address, port) = s.recvfrom(1024)

      # Try parsing the message
      try:
        message = json.loads(message.decode())
      except json.JSONDecodeError:
        bootstrap.log(termcolor.yellow(f'Invalid message received from {termcolor.underline(f"{address}:{port}")}'))
        continue

      # Check if the message is a public-key message
      if message['message_type'] == 'key':
        key = message['key']
        stake = message['stake']
        bootstrap.log(termcolor.blue(f'Received key {termcolor.underline(key[100:111])} from {termcolor.underline(f"{address}:{port}")}'))

        bootstrap.add_node(node_id, address, port, key, stake=stake)

    # Broadcast id and blockchain to all nodes
    for node in blockchain.nodes:
      if node['id'] == 0:  # Skip if node is the bootstrap
        continue

      message = json.dumps({
        'message_type': 'id',
        'id': node['id'],
        'color': next(color),
        'blockchain': dict(bootstrap.blockchain)
      })
      bootstrap.log(termcolor.magenta(f'Sending id and blockchain to node {node["id"]}'))
      s.sendto(message.encode(), (node['address'], node['port']))

    # Wait for the nodes to finish
    remaining_nodes = [node['id'] for node in blockchain.nodes if node['id'] != 0]
    while remaining_nodes:
      message, (address, port) = s.recvfrom(1024)

      # Try parsing the message
      try:
        message = json.loads(message.decode())
      except json.JSONDecodeError:
        bootstrap.log(termcolor.yellow(f'Invalid message received from {termcolor.underline(f"{address}:{port}")}'))
        continue

      if message['message_type'] == 'ack':
        remaining_nodes.remove(message['id'])
        bootstrap.log(termcolor.green(f'Node {message["id"]} ready for transactions'))

    # Distribute the coins to all nodes
    for node in blockchain.nodes:
      if node['id'] == 0:
        continue
      bootstrap.execute_transaction(node['id'], 'coins', 1000)

    bootstrap.transaction_handler.start()
    bootstrap.block_handler.start()
    bootstrap.test_messenger.start()

    # Listen for messages
    try:
      while True:
        message, (address, port) = s.recvfrom(4096*block_capacity)

        # Try parsing the message
        try:
          message = json.loads(message.decode())
        except json.JSONDecodeError:
          bootstrap.log(termcolor.yellow(f'Invalid message received from {termcolor.underline(f"{address}:{port}")}'))
          continue

        if message['message_type'] == 'transaction':
          bootstrap.log(termcolor.blue(f'Received message from {termcolor.underline(f"{address}:{port}")} (transaction)'))
          bootstrap.receive_transaction(message['transaction'])

        elif message['message_type'] == 'block':
          bootstrap.log(termcolor.blue(f'Received message from {termcolor.underline(f"{address}:{port}")} (block)'))
          bootstrap.receive_block(message['block'])

        else:
          bootstrap.log(termcolor.yellow(f'Invalid message received from {termcolor.underline(f"{address}:{port}")}'))
    except KeyboardInterrupt:
      # Terminate the process if the user interrupts it
      bootstrap.log(termcolor.blue('Process terminated by user'))
      s.close()
      return
