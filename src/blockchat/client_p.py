"""A module for a client process.

This module contains the start_node function, which is used to start a client
process of the network.
"""

import socket
import json

from node import Node
from blockchain import Blockchain

from util import termcolor

def start_node(bootstrap_address, bootstrap_port, nodes_count, verbose, debug):
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

  client = Node(verbose, debug)

  # Start the UDP server
  with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    # Bind to a random port
    s.bind(('localhost', 0))
    address, port = s.getsockname()
    client.log(termcolor.blue(f'Client node listening on {termcolor.underline(f"{address}:{port}")}'))

    # Ping boostrap node every 0.1 seconds until it responds
    s.settimeout(0.1)
    while True:
      try:
        client.log(termcolor.magenta('Pinging bootstrap node...'))
        s.sendto(b'ping', (bootstrap_address, bootstrap_port))
        message, (address, port) = s.recvfrom(1024)

        if message == b'pong' and port == bootstrap_port and address == bootstrap_address:
          break

      except socket.timeout:
        client.log(termcolor.yellow('Bootstrap node is not available. Retrying...'))
    client.log(termcolor.green('Bootstrap node is available'))
    s.settimeout(None)

    while True:
      message, (address, port) = s.recvfrom(1024)
      if message == b'ready' and port == bootstrap_port and address == bootstrap_address:
        break

    # Send the public key to the bootstrap node
    message = json.dumps({
      'message_type': 'key',
      'key': client.wallet.get_address()
    })
    client.log(termcolor.magenta('Sending key to bootstrap node'))
    s.sendto(message.encode(), ('localhost', bootstrap_port))

    while True:
      # Wait for the response containing all essential information
      message, (address, port) = s.recvfrom((nodes_count + 1)*1024)

      # Try parsing the message
      try:
        message = json.loads(message.decode())
      except json.JSONDecodeError:
        client.log(termcolor.yellow(f'Invalid message received from {termcolor.underline(f"{address}:{port}")}'))
        continue

      # Check if the message is an id message
      if message['message_type'] == 'id' and (address, port) == (bootstrap_address, bootstrap_port):
        client.id = message['id']
        client.node_color = message['color']
        client.blockchain = Blockchain(**message['blockchain'])
        client.log(termcolor.blue('Received id and blockchain from bootstrap node'))

        # Send an ack to the bootstrap node
        message = json.dumps({
          'message_type': 'ack',
          'id': client.id
        })
        s.sendto(message.encode(), (bootstrap_address, bootstrap_port))

        break

      else:
        client.log(termcolor.yellow(f'Invalid message received from {termcolor.underline(f"{address}:{port}")}'))

    # Receive initial coin transactions from bootstrap
    for i in range(nodes_count):
      while True:
        message, (address, port) = s.recvfrom(4096)

        # Try parsing the message
        try:
          message = json.loads(message.decode())
        except json.JSONDecodeError:
          client.log(termcolor.yellow(f'Invalid message received from {termcolor.underline(f"{address}:{port}")}'))
          continue

        if message['message_type'] == 'transaction':
          client.receive_transaction(message['transaction'])
          break

    client.set_stake(10)

    # Listen for messages
    try:
      while True:
        message, (address, port) = s.recvfrom(4096*client.blockchain.block_capacity)

        # Try parsing the message
        try:
          message = json.loads(message.decode())
        except json.JSONDecodeError:
          client.log(termcolor.yellow(f'Invalid message received from {termcolor.underline(f"{address}:{port}")}'))
          continue

        if message['message_type'] == 'transaction':
          client.log(termcolor.blue(f'Received message from {termcolor.underline(f"{address}:{port}")} (transaction)'))
          client.receive_transaction(message['transaction'])

        elif message['message_type'] == 'block':
          client.log(termcolor.blue(f'Received message from {termcolor.underline(f"{address}:{port}")} (block)'))
          client.receive_block(message['block'])

        else:
          client.log(termcolor.yellow(f'Invalid message received from {termcolor.underline(f"{address}:{port}")}'))
    except KeyboardInterrupt:
      # Terminate the process if the user interrupts it
      client.log(termcolor.blue('Process terminated by user'))
      s.close()
      return
