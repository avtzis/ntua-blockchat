import socket
import json

from node import Node
from blockchain import Blockchain

def start_node(bootstrap_port):
  # Create the client node
  client = Node()

  # Start the UDP server
  with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    # Bind to a random port
    s.bind(('localhost', 0))
    port = str(s.getsockname()[1])

    # Send the port and key to the bootstrap node
    message = json.dumps({
      'port': port,
      'key': client.wallet.public_key
    })
    s.sendto(message.encode(), ('localhost', bootstrap_port))

    # Wait for the response containing the id and blockchain
    message, (address, port) = s.recvfrom(2048)
    message = json.loads(message.decode())

    # Set the id and blockchain
    client.id = message.pop('id')
    client.blockchain = Blockchain(**message)
    # print(f'[NODE-{client.id}] Received blockchain {client.blockchain} from {address}')
    print(f'[NODE-{client.id}] Received blockchain from {port}')

    # Wait for the nodes list
    message, (address, port) = s.recvfrom(4096)
    client.nodes = json.loads(message.decode())
    print(f'[NODE-{client.id}] Received nodes from {port}')
