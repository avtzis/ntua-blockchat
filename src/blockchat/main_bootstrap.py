from main.cli import cli
from bootstrap import start_bootstrap
from node import Bootstrap

def main():
  nodes = 2
  capacity = 5
  address = '127.0.0.1'
  port = 5555

  bootstrap = Bootstrap(address, port, True, False, stake=0.0)
  cli.run(bootstrap, start_bootstrap, nodes_count=nodes, block_capacity=capacity)


if __name__ == '__main__':
  main()
