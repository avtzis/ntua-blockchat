import socket

import node
import blockchain

def start_bootstrap(pipe_conn, nodes, blockchain):
  # Create the bootstrap node
  bootstrap = node.Bootstrap(blockchain)

  # Create the genesis block
  bootstrap.create_genesis_block()

  # Start the UDP server
  with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    # Bind to a random port
    s.bind(('localhost', 0))
    port = s.getsockname()[1]

    # Send the port to the main process and close the connection
    pipe_conn.send(port)
    pipe_conn.close()

    # Wait for nodes to connect
    node_id = 0
    while len(bootstrap.nodes) < nodes:
      node_id += 1

      # Receive the port and key from the node
      message, address = s.recvfrom(1024)
      message = message.decode()

      # Check if the message is a port message
      if message.startswith('port'):
        # Parse the port and key from the message
        port = message.split(':')[1]
        key = message.split(':')[3]
        print(f'[BOOTSTRAP] Received port {port} and key {key} from {address}')

        # Add the node to the list
        bootstrap.add_node(port, key)

        # Send the node its id #!and current blockchain
        s.sendto(f'id:{node_id}'.encode(), address)
