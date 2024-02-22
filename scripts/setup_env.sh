#!/bin/sh

SCRIPT_PATH="$(realpath "$0")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check if the current directory is already the project root
if [ "$(pwd)" != "$PROJECT_ROOT" ]; then
  echo "Changing directory to the project root..."
  cd "$PROJECT_ROOT"
fi

# Check if the virtual environment directory exists
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  # Create the virtual environment
  python3 -m venv venv
  echo "Virtual environment created."
else
  echo "Virtual environment already exists."
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if requirements.txt exists and install dependencies
if [ -f "requirements.txt" ]; then
  echo "Installing dependencies from requirements.txt..."
  pip install -r requirements.txt
  echo "Dependencies installed."
else
  echo "requirements.txt not found. No dependencies to install."
fi
