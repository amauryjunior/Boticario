#!/usr/bin/env bash
# Runs the Smart Cane in simulated mode for a quick offline demo (no hardware needed).
set -euo pipefail
cd "$(dirname "$0")/.."
python3 src/main.py --config configs/config.yaml --simulation
