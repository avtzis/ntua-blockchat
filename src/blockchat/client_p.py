import socket

import node

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
