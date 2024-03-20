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

  bootstrap = Bootstrap(bootstrap_address, bootstrap_port, verbose, debug, blockchain, stake=10.0)

  # Get an output color for each node
  colors = termcolor.colors
  bootstrap.node_color = colors.pop(0)
  color = itertools.cycle(colors)

  bootstrap.create_genesis_block(nodes_count)
  bootstrap.add_node(0, bootstrap.wallet.get_address(), bootstrap_address, bootstrap_port, 10.0, bootstrap.nonce, bootstrap.balance)

  # Start the UDP server
  with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.bind((bootstrap_address, bootstrap_port))
    bootstrap.socket = s
    bootstrap.log(termcolor.blue(f'Listening on {termcolor.underline(f"{bootstrap_address}:{bootstrap_port}")}'))

    bootstrap.transaction_handler.start()
    bootstrap.block_handler.start()

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

        if message['message_type'] == 'ping':
          bootstrap.log(termcolor.blue(f'Ping from {termcolor.underline(f"{address}:{port}")}'))
          s.sendto(b'pong', (address, port))

        elif message['message_type'] == 'key':
          bootstrap.log(termcolor.blue(f'Received message from {termcolor.underline(f"{address}:{port}")} (key)'))

          if bootstrap.node_counter >= nodes_count:
            bootstrap.log(termcolor.yellow('Node limit reached'))
          else:
            new_node = bootstrap.add_node(bootstrap.node_counter, message['key'], address, port, message['stake'])
            bootstrap.activate_node(new_node, next(color))
            bootstrap.broadcast_node(new_node)
            bootstrap.execute_transaction(new_node['id'], 'coins', 1000.0)

            if bootstrap.node_counter == nodes_count:
              bootstrap.log(termcolor.green('All nodes connected'))
              bootstrap.test_messenger.start()

        elif message['message_type'] == 'transaction':
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
