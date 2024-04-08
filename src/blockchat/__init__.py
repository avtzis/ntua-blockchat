import argparse

from blockchat.main.cli import cli

from blockchat.client import start_node
from blockchat.bootstrap import start_bootstrap

from blockchat.node import Node, Bootstrap

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--nodes", "-n", type=int, required=True, help="Number of nodes")
  parser.add_argument("--capacity", "-c", type=int, required=True, help="Block capacity")
  parser.add_argument("--stake", "-s", type=float, default=10.0, help="Stake amount for node")
  parser.add_argument("--bootstrap", "-b", action="store_true", help="Start a bootstrap node")
  parser.add_argument("--bootstrap_address", "-a", type=str, default='0.0.0.0', help="Bootstrap node address")
  parser.add_argument("--bootstrap_port", "-p", type=int, default=5000, help="Bootstrap node port")
  parser.add_argument("--test", "-t", action="store_true", help="Run in test mode (no input required)")
  parser.add_argument("--docker", "-d", action="store_true", help="Run in docker")

  args = parser.parse_args()
  test = args.test
  docker = args.docker
  nodes = args.nodes
  capacity = args.capacity
  bootstrap = args.bootstrap
  stake = args.stake
  bootstrap_address = args.bootstrap_address if not docker else 'bootstrap-node'
  bootstrap_port = int(args.bootstrap_port) if not docker else 5000

  if bootstrap:
    if test:
      bootstrap_node = Bootstrap(bootstrap_address, bootstrap_port, debug=True, stake=stake)
      start_bootstrap(nodes, capacity, bootstrap_node, None, True)
    else:
      bootstrap_node = Bootstrap(bootstrap_address, bootstrap_port, stake=stake)
      cli.run(bootstrap_node, start_bootstrap, nodes_count=nodes, block_capacity=capacity)
  else:
    if test:
      client_node = Node(bootstrap_address, bootstrap_port, debug=True, stake=stake)
      start_node(nodes, capacity, client_node, None, True)
    else:
      client_node = Node(bootstrap_address, bootstrap_port, stake=stake)
      cli.run(client_node, start_node, nodes_count=nodes, block_capacity=capacity)
