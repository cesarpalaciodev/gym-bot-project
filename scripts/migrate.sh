#!/bin/bash
# Database migration script

set -e

COMMAND=${1:-status}

# Check if virtual environment exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

case $COMMAND in
    status)
        echo "📊 Migration status:"
        python -m utils.migrate status
        ;;
    upgrade)
        echo "⬆️  Running migrations..."
        python -m utils.migrate upgrade
        ;;
    downgrade)
        echo "⬇️  Rolling back migrations..."
        python -m utils.migrate rollback --steps ${2:-1}
        ;;
    *)
        echo "Usage: $0 {status|upgrade|downgrade [steps]}"
        exit 1
        ;;
esac