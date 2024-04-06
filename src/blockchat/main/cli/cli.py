from threading import Thread
from queue import Queue

from prompt_toolkit import prompt

help_message = """
Available commands:
  transaction <node> <type> <value>: Send a transaction. Available types: 'coins', 'message'
  stake <value>: Stake an amount of coins
  balance: Show the current balance
  view: View last block
  help: Show this help text
  exit: Exit the client
"""

welcome_message = """Welcome to BlockChat!

Connecting to blockchain network...
"""

prompt_message = """
Type 'help' to see the available commands."""

def run(client, node_process_func, **kwargs):
  print(welcome_message)

  ready_queue = Queue()
  node_thread = Thread(
    target=node_process_func,
    args=(kwargs['nodes_count'], kwargs['block_capacity'], client, ready_queue,)
  )
  node_thread.daemon = True
  node_thread.start()

  try:
    ready_queue.get()
  except KeyboardInterrupt:
    print('Exiting')
    client.delete_logfile()
    return

  print(prompt_message)

  while True:
    try:
      input = prompt('>>> ')

      if input.startswith('exit'):
        raise EOFError

      elif input.startswith('help'):
        print(help_message)

      elif input.startswith('balance'):
        print(f'Current balance: {client.wallet.balance} BCC')

      elif input.startswith('view'):
        print(client.blockchain.get_last_block())

      elif input.startswith('transaction'):
        _, node, type, value = input.split(' ', 3)

        # Check if all arguments are provided
        if not node or not type or not value:
          print('Missing transaction arguments')
          print('Usage: transaction <node> <type> <value>')
          continue

        node = int(node)
        if type == 'coins':
          value = int(value)

        client.execute_transaction(node, type, value)

      elif input.startswith('stake'):
        _, value = input.split(' ', 1)

        # Check if all arguments are provided
        if not value:
          print('Missing stake amount')
          print('Usage: stake <value>')
          continue

        client.set_stake(value)

      else:
        print('Invalid command\n')
        print(help_message)

    except (KeyboardInterrupt, EOFError):
      print('Exiting')
      client.delete_logfile()
      return
