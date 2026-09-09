#!/usr/bin/env bash
set -e

if [ -z "$1" ]; then
    echo "Error: Commit message required."
    echo "Usage: ./scripts/commit-stage.sh 'feat: describe changes'"
    exit 1
fi

git add -A
git commit -m "$1" || echo "Nothing to commit"
echo "Committed: $1"
