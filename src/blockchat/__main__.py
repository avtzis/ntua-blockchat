import argparse


import socket
import multiprocessing

import node
import blockchain

from bootstrap_p import start_bootstrap
from client_p import start_node

def main():

  parser = argparse.ArgumentParser()
  #defining arguments
  parser.add_argument("--nodes","-n" ,type=int,required=True, help="Number of nodes")
  parser.add_argument("--capacity","-c" ,type=int,required=True, help="Capacity")
  #parse arguments
  args = parser.parse_args()

  nodes = args.nodes
  capacity = args.capacity

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
