"""A module for the Bootstrap process.

This module contains the start_bootstrap function, which is used to start the
bootstrap process of the network.
"""

import socket
import json
import itertools

from blockchain import Blockchain

from util import termcolor

def start_bootstrap(nodes_count, block_capacity, bootstrap, ready_queue=None, test_flag=False):
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

  # Get an output color for each node
  colors = termcolor.colors
  bootstrap.node_color = colors.pop(0)
  color = itertools.cycle(colors)

  blockchain = Blockchain(block_capacity)
  bootstrap.blockchain = blockchain
  bootstrap.log(termcolor.blue('Blockchain created'))

  bootstrap_address, bootstrap_port = bootstrap.bootstrap_address, bootstrap.bootstrap_port

  bootstrap.create_genesis_block(nodes_count)
  bootstrap.add_node(0, bootstrap.wallet.get_address(), bootstrap_address, bootstrap_port, 10.0, bootstrap.nonce, bootstrap.wallet.balance)

  # Start the UDP server
  with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.bind(('0.0.0.0', bootstrap_port))
    address, port = s.getsockname()
    bootstrap.socket = s
    bootstrap.log(termcolor.blue(f'Listening on {termcolor.underline(f"{address}:{port}")}'))

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
          bootstrap.log(termcolor.yellow(f'Invalid message received from {termcolor.underline(f"{address}:{port}")}'), not bootstrap.debug)
          continue

        if message['message_type'] == 'ping':
          bootstrap.log(termcolor.blue(f'Ping from {termcolor.underline(f"{address}:{port}")}'))
          s.sendto(b'pong', (address, port))

        elif message['message_type'] == 'key':
          bootstrap.log(termcolor.blue(f'Received message from {termcolor.underline(f"{address}:{port}")} (key)'))

          if bootstrap.node_counter >= nodes_count:
            bootstrap.log(termcolor.yellow('Node limit reached'), not bootstrap.debug)
          else:
            new_node = bootstrap.add_node(bootstrap.node_counter, message['key'], address, port, message['stake'])
            bootstrap.activate_node(new_node, next(color))
            bootstrap.broadcast_node(new_node)
            bootstrap.execute_transaction(new_node['id'], 'coins', 1000.0)

            # Start the test messenger when all nodes have connected
            if bootstrap.node_counter == nodes_count:
              bootstrap.log(termcolor.green('All nodes connected'))

              if ready_queue:
                ready_queue.put('ready')

              if test_flag:
                bootstrap.test_messenger.start()

        elif message['message_type'] == 'transaction':
          bootstrap.log(termcolor.blue(f'Received message from {termcolor.underline(f"{address}:{port}")} (transaction)'), not bootstrap.debug)
          bootstrap.receive_transaction(message['transaction'])

        elif message['message_type'] == 'block':
          bootstrap.log(termcolor.blue(f'Received message from {termcolor.underline(f"{address}:{port}")} (block)'), not bootstrap.debug)
          bootstrap.receive_block(message['block'])

        else:
          bootstrap.log(termcolor.yellow(f'Invalid message received from {termcolor.underline(f"{address}:{port}")}'), not bootstrap.debug)
    except KeyboardInterrupt:
      # Terminate the process if the user interrupts it
      bootstrap.log(termcolor.blue('Process terminated by user'))
      s.close()
      return
