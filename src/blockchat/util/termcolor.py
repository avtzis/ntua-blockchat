# ANSI escape codes for colors
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
MAGENTA = '\033[95m'
CYAN = '\033[96m'
WHITE = '\033[97m'
RESET_COLOR = '\033[0m'

BOLD = '\033[1m'
RESET_BOLD = '\033[22m'

UNDERLINE = '\033[4m'
RESET_UNDERLINE = '\033[24m'

colors = [RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN]

def red(s):
  return RED + s + RESET_COLOR

def green(s):
  return GREEN + s + RESET_COLOR

def yellow(s):
  return YELLOW + s + RESET_COLOR

def blue(s):
  return BLUE + s + RESET_COLOR

def magenta(s):
  return MAGENTA + s + RESET_COLOR

def cyan(s):
  return CYAN + s + RESET_COLOR

def white(s):
  return WHITE + s + RESET_COLOR

def bold(s):
  return BOLD + s + RESET_BOLD

def underline(s):
  return UNDERLINE + s + RESET_UNDERLINE
