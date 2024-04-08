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

  args = parser.parse_args()
  nodes = args.nodes
  capacity = args.capacity
  bootstrap = args.bootstrap
  stake = args.stake
  bootstrap_address = args.bootstrap_address
  bootstrap_port = int(args.bootstrap_port)

  if bootstrap:
    bootstrap_node = Bootstrap(bootstrap_address, bootstrap_port, stake=stake)
    cli.run(bootstrap_node, start_bootstrap, nodes_count=nodes, block_capacity=capacity)
  else:
    client_node = Node(bootstrap_address, bootstrap_port, stake=stake)
    cli.run(client_node, start_node, nodes_count=nodes, block_capacity=capacity)
