import socket
import json

from node import Bootstrap
# import blockchain

def start_bootstrap(pipe_conn, nodes, blockchain):
  # Create the bootstrap node
  bootstrap = Bootstrap(blockchain)

  # Create the genesis block
  bootstrap.create_genesis_block(nodes)
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
    while len(bootstrap.nodes) < nodes:
      node_id += 1

      # Receive the key from the node
      message, (address, port) = s.recvfrom(1024)
      message = json.loads(message.decode())

      # Check if the message is a public-key message
      if message.get('key') is not None:
        key = message['key']
        print(f'[BOOTSTRAP] Received key {key[100:111]} from {port}')

        # Add the node to the list
        bootstrap.add_node(node_id, address, port, key)

        # Send the node its id and current blockchain
        message = dict(bootstrap.blockchain)
        message['id'] = node_id
        s.sendto(json.dumps(message).encode(), (address, port))

    # Broadcast node information to all nodes
    for node in bootstrap.nodes:
      s.sendto(json.dumps(bootstrap.nodes).encode(), (node['address'], node['port']))
