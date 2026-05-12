#!/bin/bash
# Local simulation of the GitHub Pages deployment pipeline
set -e

# Configuration
PROJECT_ROOT=$(pwd)
PYTHON_EXEC=".venv/bin/python3"
WEB_DIR="web"

echo "🚀 Starting NepSense Local Deploy Simulation..."

# 1. Update Python Data Pipeline
echo "📊 Running Analytical Pipeline (daily-run)..."
export PYTHONPATH=$PYTHONPATH:$PROJECT_ROOT/src
$PYTHON_EXEC src/nepsense/cli.py daily-run

# 1.5 Generate Broker Intelligence Data
echo "🕵️ Generating Broker Intelligence patterns..."
$PYTHON_EXEC src/nepsense/ml/generate_broker_dashboard_data.py

# 2. Build React Frontend
echo "🏗️ Building Vite frontend..."
cd "$WEB_DIR"
npm install
# Set VITE_BASE_PATH to empty for local testing or relative paths
VITE_BASE_PATH="" npm run build

echo ""
echo "✨ Local Simulation Complete!"
echo "📍 Dashboard artifacts are in: $WEB_DIR/dist"
echo "👉 To preview the production build, run: npx serve -s dist"
