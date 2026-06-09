#!/bin/bash

set -e

RELEASE_DIR="releases"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
ARCHIVE_NAME="book-shelf-release-$TIMESTAMP.tar.gz"

mkdir -p "$PROJECT_ROOT/$RELEASE_DIR"

tar -czf "$PROJECT_ROOT/$RELEASE_DIR/$ARCHIVE_NAME" \
    --exclude='__pycache__' \
    -C "$PROJECT_ROOT/src" .

echo "✅ Релиз создан: $RELEASE_DIR/$ARCHIVE_NAME"
