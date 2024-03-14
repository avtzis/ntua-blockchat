import socket
import json

from node import Bootstrap
# import blockchain

def start_bootstrap(pipe_conn, nodes_count, blockchain):
  # Create the bootstrap node
  bootstrap = Bootstrap(blockchain)

  # Create the genesis block
  bootstrap.create_genesis_block(nodes_count)
  # print('[BOOTSTRAP] Blockchain: ', bootstrap.blockchain)

  # Start the UDP server
  with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    # Bind to a random port
    s.bind(('localhost', 0))
    port = s.getsockname()[1]
    bootstrap.socket = s

    # Add bootstrap to the list of nodes
    bootstrap.add_node(0, 'localhost', port, bootstrap.wallet.get_address(), bootstrap.nonce, bootstrap.balance)

    # Send the port to the main process and close the pipe
    pipe_conn.send(port)
    pipe_conn.close()

    # Wait for nodes to connect
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
    blockchain.nodes.pop(0)
    remaining_nodes = [node['id'] for node in blockchain.nodes]
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
      bootstrap.execute_transaction(node['id'], 'coins', 1000)
