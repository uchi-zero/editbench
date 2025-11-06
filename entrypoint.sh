#!/bin/bash
set -e

# Setup uv environment if it doesn't exist or is broken
if [ ! -d "/root/.docker_env" ] || [ ! -f "/root/.docker_env/bin/python3" ] || ! /root/.docker_env/bin/python3 --version &>/dev/null; then
    echo "Setting up Python environment with uv (Python $PYTHON_VERSION)..."
    rm -rf /root/.docker_env  # Remove any broken environment
    uv venv --python $PYTHON_VERSION /root/.docker_env
fi

# Activate the environment
source /root/.docker_env/bin/activate

# Install dependencies if pyproject.toml or setup.py exists
if [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
    echo "Installing Python dependencies..."
    uv pip install -e .
fi

# Execute the command passed to the container
exec "$@"