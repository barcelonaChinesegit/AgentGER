#!/bin/bash
# One-command launcher for the AgentGER web frontend demo.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$ROOT_DIR"
exec ./web/start.sh
