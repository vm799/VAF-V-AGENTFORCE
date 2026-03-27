#!/bin/bash
# VAF Enterprise Demo — one command, full pipeline, dashboard open
# Usage: ./enterprise/demo.sh

cd "$(dirname "$0")"
echo "🏢 VAF Enterprise Pipeline Demo"
echo "================================"
echo "Running all 9 builds..."
python3 orchestrator.py run --mode with-dashboard
echo ""
echo "Opening dashboard..."
open outputs/dashboard.html
echo ""
echo "Demo complete. Screenshot outputs/dashboard.html for LinkedIn/press."
