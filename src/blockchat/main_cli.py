from main.cli import cli
from client_p import start_node
from node import Node

def main():
  nodes = 4
  capacity = 5
  address = '127.0.0.1'
  port = 5555

  client = Node(address, port, True, False, stake=0.0)
  cli.run(client, start_node, nodes_count=nodes, block_capacity=capacity)


if __name__ == '__main__':
  main()
