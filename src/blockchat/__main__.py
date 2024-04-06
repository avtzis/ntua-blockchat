import argparse
import multiprocessing

from bootstrap_p import start_bootstrap
from client_p import start_node
from node import Node, Bootstrap

from util import termcolor

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--nodes", "-n", type=int, required=True, help="Number of nodes")
  parser.add_argument("--capacity", "-c", type=int, required=True, help="Block capacity")
  parser.add_argument("--address", "-a", type=str, default='127.0.0.1', help="Bootstrap address")
  parser.add_argument("--port", "-p", type=int, default=5555, help="Bootstrap port")
  parser.add_argument("--verbose", "-v", action="store_true", help="Increase output verbosity")
  parser.add_argument("--debug", "-d", action="store_true", help="Enable debug mode")
  args = parser.parse_args()

  nodes = args.nodes
  capacity = args.capacity
  address = args.address
  port = args.port
  verbose = args.verbose
  debug = args.debug

  try:
    # Start the bootstrap process
    bootstrap = Bootstrap(address, port, verbose, debug, stake=10.0)
    bootstrap_process = multiprocessing.Process(
      target=start_bootstrap,
      args=(nodes, capacity, bootstrap, None, True)
    )
    processes = [bootstrap_process]
    print(termcolor.bold('[INIT]'), termcolor.magenta('Starting bootstrap process'))
    bootstrap_process.start()

    # Start the client processes
    for i in range(nodes - 1):
      node = Node(address, port, verbose, debug, stake=10.0)
      node_process = multiprocessing.Process(
        target=start_node,
        args=(nodes, capacity, node, None, True)
      )
      processes.append(node_process)
      print(termcolor.bold('[INIT]'), termcolor.magenta(f'Starting client process {i}'))
      node_process.start()

    # Wait for all processes to finish
    for process in processes:
      process.join()

  except KeyboardInterrupt:
    # Wait for all processes to finish
    for process in processes:
      process.join()

    print(termcolor.bold('[INIT]'), termcolor.green('All processes finished'))
    print(termcolor.bold('[INIT]'), termcolor.magenta('Exiting'))


if __name__ == '__main__':
  main()
