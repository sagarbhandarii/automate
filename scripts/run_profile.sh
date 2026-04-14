#!/usr/bin/env bash
set -euo pipefail
PROFILE="${1:-smoke}"
python -m mstf.main --profile "${PROFILE}"
