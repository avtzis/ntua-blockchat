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

    # Send the port to the main process and close the pipe
    pipe_conn.send(port)
    pipe_conn.close()

    # Wait for nodes to connect
    node_id = 0
    while len(blockchain.nodes) < nodes_count:
      node_id += 1

      # Receive the key from the node
      message, (address, port) = s.recvfrom(1024)
      message = json.loads(message.decode())

      # Check if the message is a public-key message
      if message['message_type'] == 'key':
        key = message['key']
        print(f'[BOOTSTRAP] Received key {key[100:111]} from {port}')

        # Add the node to the list
        bootstrap.add_node(node_id, address, port, key)

    # Broadcast id and blockchain to all nodes
    for node in blockchain.nodes:
      message = json.dumps({
        'message_type': 'id',
        'id': node['id'],
        'blockchain': dict(bootstrap.blockchain)
      })
      s.sendto(message.encode(), (node['address'], node['port']))

    # Wait for the nodes to finish
    remaining_nodes = [node['id'] for node in blockchain.nodes]
    while remaining_nodes:
      message, (address, port) = s.recvfrom(1024)
      message = json.loads(message.decode())

      if message['message_type'] == 'ack':
        remaining_nodes.remove(message['id'])
        print(f'[BOOTSTRAP] Node {message["id"]} ready')
