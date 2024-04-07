import argparse

from client import start_node
from bootstrap import start_bootstrap

from node import Node, Bootstrap

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--nodes", "-n", type=int, required=True, help="Number of nodes")
  parser.add_argument("--capacity", "-c", type=int, required=True, help="Block capacity")
  parser.add_argument("--stake", "-s", type=float, default=10.0, help="Stake amount for node")
  parser.add_argument("--bootstrap", "-b", action="store_true", help="Start a bootstrap node")

  args = parser.parse_args()
  nodes = args.nodes
  capacity = args.capacity
  bootstrap = args.bootstrap
  stake = args.stake

  bootstrap_address = 'bootstrap-node'
  # bootstrap_port = 5000

  if bootstrap:
    bootstrap_node = Bootstrap(bootstrap_address, debug=True, stake=stake)
    start_bootstrap(nodes, capacity, bootstrap_node, None, True)
  else:
    client_node = Node(bootstrap_address, debug=True, stake=stake)
    start_node(nodes, capacity, client_node, None, True, port=5000)


if __name__ == '__main__':
  main()
