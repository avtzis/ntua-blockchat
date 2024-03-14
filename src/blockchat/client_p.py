import socket
import json

from node import Node
from blockchain import Blockchain

def start_node(bootstrap_address, bootstrap_port, nodes_count):
  # Create the client node
  client = Node()

  # Start the UDP server
  with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    # Bind to a random port
    s.bind(('localhost', 0))
    address, port = s.getsockname()
    client.socket = s
    print(f'[NODE] Client node listening on {address}:{port}')

    # Check if bootstrap is available
    s.settimeout(0.1)
    while True:
      try:
        print('[NODE] Pinging bootstrap node...')
        s.sendto(b'ping', (bootstrap_address, bootstrap_port))
        message, (address, port) = s.recvfrom(1024)

        if message == b'pong' and port == bootstrap_port and address == bootstrap_address:
          break

      except socket.timeout:
        print('[NODE] Bootstrap node is not available. Retrying...')
    print('[NODE] Bootstrap node is available')
    s.settimeout(None)

    while True:
      message, (address, port) = s.recvfrom(1024)
      if message == b'ready' and port == bootstrap_port and address == bootstrap_address:
        break

    # Send the wallet key to the bootstrap node
    message = json.dumps({
      'message_type': 'key',
      'key': client.wallet.get_address()
    })
    print('[NODE] Sending key to bootstrap node')
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

    # Stake the coins
    client.set_stake(10)

    # Listen for messages
    try:
      while True:
        message, (address, port) = s.recvfrom(4096*client.blockchain.block_capacity)

        # Try parsing the message
        try:
          message = json.loads(message.decode())
        except json.JSONDecodeError:
          print(f'[NODE-{client.id}] Invalid message received')
          continue

        if message['message_type'] == 'transaction':
          client.receive_transaction(message['transaction'])

        elif message['message_type'] == 'block':
          client.receive_block(message['block'])

        else:
          print(f'[NODE-{client.id}] Invalid message received')
    except KeyboardInterrupt:
      print(f'[NODE-{client.id}] Client process terminated by user')
      s.close()
      return
