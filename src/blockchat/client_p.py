import socket
import json

from node import Node
from blockchain import Blockchain

def start_node(bootstrap_port, nodes_count):
  # Create the client node
  client = Node()

  # Start the UDP server
  with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    # Bind to a random port
    s.bind(('localhost', 0))
    port = str(s.getsockname()[1])
    client.socket = s

    # Send the wallet key to the bootstrap node
    message = json.dumps({
      'message_type': 'key',
      'key': client.wallet.get_address()
    })
    s.sendto(message.encode(), ('localhost', bootstrap_port))

    while True:
      # Wait for the response containing all essential information
      message, (address, port) = s.recvfrom((nodes_count + 1)*1024)

      # Try parsing the message
      try:
        message = json.loads(message.decode())
      except json.JSONDecodeError:
        print(f'[NODE-{client.id}] Invalid message received')
        continue

      # Check if the message is an id message
      if message['message_type'] == 'id':
        # Set the id
        client.id = message['id']

        # Set the blockchain
        client.blockchain = Blockchain(**message['blockchain'])
        print(f'[NODE-{client.id}] Received id and blockchain from {port}')

        # if client.id == 1:
        #   print(f'[NODE-{client.id}] Blockchain: {client.blockchain}')
        #   print(f'[NODE-{client.id}] Nodes: {client.blockchain.nodes}')

        # Send an ack to the bootstrap node
        message = json.dumps({
          'message_type': 'ack',
          'id': client.id
        })
        s.sendto(message.encode(), ('localhost', bootstrap_port))

        break

      else:
        print(f'[NODE-{client.id}] Invalid message received')

    # Receive initial coin transactions from bootstrap
    for i in range(nodes_count):
      while True:
        message, (address, port) = s.recvfrom(4096)

        try:
          message = json.loads(message.decode())
        except json.JSONDecodeError:
          print(f'[NODE-{client.id}] Invalid message received')
          continue

        if message['message_type'] == 'transaction':
          client.receive_transaction(message['transaction'])
          break
