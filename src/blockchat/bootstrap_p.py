import socket
import json
import itertools

from node import Bootstrap
from blockchain import Blockchain

from util import termcolor

def start_bootstrap(nodes_count, block_capacity, bootstrap_address, bootstrap_port, verbose, debug):
  # Create the blockchain
  blockchain = Blockchain(block_capacity)
  print(termcolor.red('[BOOTSTRAP]'), termcolor.blue('Blockchain created'))

  # Create the bootstrap node
  bootstrap = Bootstrap(verbose, debug, blockchain)

  colors = termcolor.colors
  bootstrap.node_color = colors.pop(0)
  color = itertools.cycle(colors)

  # Create the genesis block
  bootstrap.create_genesis_block(nodes_count)
  # print('[BOOTSTRAP] Blockchain: ', bootstrap.blockchain)

  # Start the UDP server
  with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    # Bind to the specified address and port
    s.bind((bootstrap_address, bootstrap_port))
    address, port = s.getsockname()
    bootstrap.socket = s
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

    # Add bootstrap to the list of nodes
    bootstrap.add_node(0, bootstrap_address, bootstrap_port, bootstrap.wallet.get_address(), bootstrap.nonce, bootstrap.balance)

    # Wait for the nodes to send their public keys
    node_id = 0
    while len(blockchain.nodes) - 1 < nodes_count:
      node_id += 1

      # Receive the key from the node
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
        bootstrap.log(termcolor.blue(f'Received key {termcolor.underline(key[100:111])} from {termcolor.underline(f"{address}:{port}")}'))

        # Add the node to the list
        bootstrap.add_node(node_id, address, port, key)

    # Broadcast id and blockchain to all nodes
    for node in blockchain.nodes:
      # Skip if node is the bootstrap
      if node['id'] == 0:
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
      bootstrap.log(termcolor.blue('Process terminated by user'))
      s.close()
      return
