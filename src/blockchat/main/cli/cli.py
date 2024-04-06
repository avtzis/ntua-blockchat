import subprocess

from threading import Thread
from queue import Queue

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter

help_message = """
Available commands:
  transaction <node> <type> <value>: Send a transaction. Available types: 'coins', 'message'
  stake <value>: Stake an amount of coins
  balance: Show the current balance
  view: View last block
  help: Show this help text
  exit: Exit the client
  history: Show transaction history
  logs: Show logs"""

welcome_message = """Welcome to BlockChat!

Connecting to blockchain network...
"""

prompt_message = """
Type 'help' to see the available commands."""

def run(client, node_process_func, **kwargs):
  session = PromptSession()
  completer = WordCompleter(['transaction', 'stake', 'balance', 'view', 'help', 'exit', 'history', 'logs', 'message', 'coins'])

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
      input = session.prompt('\n>>> ', completer=completer, complete_while_typing=False, enable_history_search=True)

      if input == '':
        continue

      elif input.startswith('exit'):
        raise EOFError

      elif input.startswith('help'):
        print(help_message)

      elif input.startswith('balance'):
        print(f'Current balance: {client.wallet.balance} BCC')

      elif input.startswith('view'):
        print(client.blockchain.get_last_block())

      elif input.startswith('transaction'):
        try:
          _, node, type, value = input.split(' ', 3)
        except ValueError:
          print('Missing transaction arguments')
          print('Usage: transaction <node> <type> <value>')
          continue

        node = int(node)
        if type == 'coins':
          value = int(value)

        client.execute_transaction(node, type, value)

      elif input.startswith('stake'):
        try:
          _, value = input.split(' ', 1)
        except ValueError:
          print('Missing stake amount')
          print('Usage: stake <value>')
          continue

        client.set_stake(float(value))

      elif input.startswith('logs'):
        try:
          subprocess.run(['less', client.log_file], check=True)
        except subprocess.CalledProcessError:
          print('Failed to open logs')

      elif input.startswith('history'):
        print(client.history)

      else:
        print('Invalid command\n')
        print(help_message)

    except (KeyboardInterrupt, EOFError):
      print('Exiting')
      client.delete_logfile()
      return
