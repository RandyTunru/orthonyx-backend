#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Run the database migrations
echo "Running database migrations..."
alembic upgrade head

# Execute the main container command (passed as arguments to this script)
# The "exec" command replaces the shell process with the one specified,
# ensuring Uvicorn receives signals correctly.
exec "$@"