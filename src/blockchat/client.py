"""A module for a client process.

This module contains the start_node function, which is used to start a client
process of the network.
"""

import socket
import json
import time

from blockchain import Blockchain
from transaction import Transaction

from util import termcolor

def start_node(nodes_count, block_capacity, client, ready_queue=None, test_flag=False, port=0):
  """Starts a client process.

  This function starts a client process, which is used to connect to the network
  and send and receive messages.

  Args:
    bootstrap_address (str): The address of the bootstrap node.
    bootstrap_port (int): The port of the bootstrap node.
    nodes_count (int): The number of nodes in the network.
    verbose (bool): Whether to enable verbose mode.
    debug (bool): Whether to enable debug mode.
  """

  # Start the UDP server
  with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    # Bind to a random port
    s.bind(('0.0.0.0', port))
    address, port = s.getsockname()
    client.socket = s
    client.log(termcolor.blue(f'Client node listening on {termcolor.underline(f"{address}:{port}")}'))

    # Ping bootstrap to see if it is
    try:
      client.ping_bootstrap()
    except KeyboardInterrupt:
      client.log(termcolor.yellow('Connection could not be established with bootstrap node'))
      client.log(termcolor.blue('Process terminated by user'))
      s.close()
      return

    # Send public-key to bootstrap to get an id
    client.send_key()

    # Flag to signal when the client is ready
    ready_flag = True

    # Listen for messages
    try:
      while True:
        # Signal ready to CLI or start the test messenger
        if ready_flag and client.node_counter == nodes_count:
          ready_flag = False
          client.log(termcolor.green('All nodes connected'))
          client.log(termcolor.blue('Ready to send transactions'))

          if ready_queue:
            ready_queue.put('ready')

          time.sleep(0.1)

          if test_flag:
            client.test_messenger.start()

        message, (address, port) = s.recvfrom(4096*block_capacity)

        # Try parsing the message
        try:
          message = json.loads(message.decode())
        except json.JSONDecodeError:
          client.log(termcolor.yellow(f'Invalid message received from {termcolor.underline(f"{address}:{port}")}'), not client.debug)
          continue

        if message['message_type'] == 'activate' and (address, port) == (client.bootstrap_address, client.bootstrap_port):
          client.log(termcolor.blue(f'Received message from {termcolor.underline(f"{address}:{port}")} (activate)'))
          client.log(termcolor.blue('Received id and blockchain from bootstrap node'))
          client.id = message['id']
          client.node_color = message['color']

          blockchain = Blockchain(**message['blockchain'])
          client.validate_chain(blockchain)
          client.blockchain = blockchain
          client.node_counter = len(client.blockchain.nodes)
          client.current_block = [Transaction(**transaction) for transaction in message['current_block']]
          client.log(termcolor.magenta('Waiting for all nodes to connect...'))

          client.transaction_handler.start()
          client.block_handler.start()

        elif message['message_type'] == 'node' and (address, port) == (client.bootstrap_address, client.bootstrap_port):
          client.log(termcolor.blue(f'Received message from {termcolor.underline(f"{address}:{port}")} (node)'), not client.debug)
          client.add_node(**message['node'])

        elif message['message_type'] == 'transaction':
          client.log(termcolor.blue(f'Received message from {termcolor.underline(f"{address}:{port}")} (transaction)'), not client.debug)
          client.receive_transaction(message['transaction'])

        elif message['message_type'] == 'block':
          client.log(termcolor.blue(f'Received message from {termcolor.underline(f"{address}:{port}")} (block)'), not client.debug)
          client.receive_block(message['block'])

        else:
          client.log(termcolor.yellow(f'Invalid message received from {termcolor.underline(f"{address}:{port}")} (type: {message["message_type"]})'), not client.debug)
    except KeyboardInterrupt:
      # Terminate the process if the user interrupts it
      client.log(termcolor.blue('Process terminated by user'))
      s.close()
      return
