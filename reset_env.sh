#!/usr/bin/env bash
# reset_env.sh — Wipe and rebuild the Python virtual environment.
#
# Usage:
#   bash reset_env.sh
#
# What it does:
#   1. Removes the existing .venv directory (if present).
#   2. Creates a fresh virtual environment in .venv using the Python 3
#      interpreter found on PATH (must be 3.10 or later).
#   3. Installs all packages listed in requirements.txt into the new
#      environment.
#
# After the script finishes, activate the environment and run any script:
#   source .venv/bin/activate      # macOS / Linux
#   .venv\Scripts\activate         # Windows (run reset_env.sh via Git Bash)
#   python mono_channel_visualizer.py

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
REQUIREMENTS="$SCRIPT_DIR/requirements.txt"

# ---------------------------------------------------------------------------
# 1. Verify Python version
# ---------------------------------------------------------------------------
PYTHON=$(command -v python3 || command -v python)

PY_VERSION=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$("$PYTHON" -c "import sys; print(sys.version_info.major)")
PY_MINOR=$("$PYTHON" -c "import sys; print(sys.version_info.minor)")

if [[ "$PY_MAJOR" -lt 3 || ( "$PY_MAJOR" -eq 3 && "$PY_MINOR" -lt 10 ) ]]; then
    echo "ERROR: Python 3.10 or later is required (found $PY_VERSION)." >&2
    exit 1
fi

echo "Using Python $PY_VERSION ($PYTHON)"

# ---------------------------------------------------------------------------
# 2. Remove the old virtual environment
# ---------------------------------------------------------------------------
if [[ -d "$VENV_DIR" ]]; then
    echo "Removing existing virtual environment at $VENV_DIR ..."
    rm -rf "$VENV_DIR"
fi

# ---------------------------------------------------------------------------
# 3. Create a fresh virtual environment
# ---------------------------------------------------------------------------
echo "Creating new virtual environment ..."
"$PYTHON" -m venv "$VENV_DIR"

# ---------------------------------------------------------------------------
# 4. Install dependencies
# ---------------------------------------------------------------------------
echo "Installing dependencies from $REQUIREMENTS ..."
"$VENV_DIR/bin/pip" install --upgrade pip --quiet
"$VENV_DIR/bin/pip" install -r "$REQUIREMENTS"

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo ""
echo "Environment ready. Activate it with:"
echo "  source .venv/bin/activate      # macOS / Linux"
echo "  .venv\\Scripts\\activate         # Windows (Git Bash)"
