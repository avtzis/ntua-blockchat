# import sys
import socket
import multiprocessing

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


def start_node(bootstrap_port):
  # Create the client node
  client = node.Node()

  # Start the UDP server
  with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    # Bind to a random port
    s.bind(('localhost', 0))
    port = str(s.getsockname()[1])

    # Send the port and key to the bootstrap node
    message = f'port:{port}:key:{client.wallet.public_key}'
    s.sendto(message.encode(), ('localhost', bootstrap_port))

    # Receive the id from the bootstrap node
    message, address = s.recvfrom(1024)
    client.id = int(message.decode().split(':')[1])
    print(f'[NODE-{client.id}] Received id {client.id} from {address}')

def main():
  #!implement argument parsing
  nodes = 5
  capacity = 10

  # Create the blockchain
  bc = blockchain.Blockchain(capacity)

  # Start the bootstrap process
  parent_conn, child_conn = multiprocessing.Pipe()
  bootstrap_process = multiprocessing.Process(
    target=start_bootstrap,
    args=(child_conn, nodes, bc,)
  )
  print('[INIT] Starting bootstrap process')
  bootstrap_process.start()

  # Receive the bootstrap port from the bootstrap process to start the nodes
  bootstrap_port = int(parent_conn.recv())

  # Start the client processes
  for i in range(nodes):
    node_process = multiprocessing.Process(
      target=start_node,
      args=(bootstrap_port,)
    )
    node_process.start()

  # Wait for the bootstrap process to terminate
  bootstrap_process.join()
  print('[INIT] Bootstrap process terminated')
  print('[INIT] Program will now exit.')

if __name__ == '__main__':
  main()
