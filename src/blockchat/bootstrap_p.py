import socket
import json

from node import Bootstrap
from blockchain import Blockchain

def start_bootstrap(nodes_count, block_capacity, bootstrap_address, bootstrap_port):
  # Create the blockchain
  blockchain = Blockchain(block_capacity)
  print('[BOOTSTRAP] Blockchain created')

  # Create the bootstrap node
  bootstrap = Bootstrap(blockchain)

  # Create the genesis block
  bootstrap.create_genesis_block(nodes_count)
  print('[BOOTSTRAP] Genesis block created')
  # print('[BOOTSTRAP] Blockchain: ', bootstrap.blockchain)

  # Start the UDP server
  with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    # Bind to the specified address and port
    s.bind((bootstrap_address, bootstrap_port))
    address, port = s.getsockname()
    bootstrap.socket = s
    print(f'[BOOTSTRAP] Bootstrap node listening on {address}:{port}')

    # Wait for the nodes to connect
    addresses = []
    for i in range(nodes_count):
      while True:
        message, (address, port) = s.recvfrom(1024)
        if message == b'ping' and (address, port) not in addresses:
          s.sendto(b'pong', (address, port))
          addresses.append((address, port))
          print(f'[BOOTSTRAP] Connected: {addresses}')
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
        print(f'[BOOTSTRAP] Invalid message received from {port}')
        continue

      # Check if the message is a public-key message
      if message['message_type'] == 'key':
        key = message['key']
        print(f'[BOOTSTRAP] Received key {key[100:111]} from {port}')

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
        'blockchain': dict(bootstrap.blockchain)
      })
      s.sendto(message.encode(), (node['address'], node['port']))

    # Wait for the nodes to finish
    remaining_nodes = [node['id'] for node in blockchain.nodes if node['id'] != 0]
    while remaining_nodes:
      message, (address, port) = s.recvfrom(1024)

      # Try parsing the message
      try:
        message = json.loads(message.decode())
      except json.JSONDecodeError:
        print(f'[BOOTSTRAP] Invalid message received from {port}')
        continue

      if message['message_type'] == 'ack':
        remaining_nodes.remove(message['id'])
        print(f'[BOOTSTRAP] Node {message["id"]} ready for transactions')

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
          print(f'[BOOTSTRAP] Invalid message received from {port}')
          continue

        if message['message_type'] == 'transaction':
          print(f'[BOOTSTRAP] Received transaction from {port}')
          bootstrap.receive_transaction(message['transaction'])

        elif message['message_type'] == 'block':
          print(f'[BOOTSTRAP] Received block from {port}')
          bootstrap.receive_block(message['block'])

        else:
          print(f'[BOOTSTRAP] Invalid message received from {port}')
    except KeyboardInterrupt:
      print('[BOOTSTRAP] Bootstrap process terminated by user')
      s.close()
      return
