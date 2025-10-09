#!/bin/bash

# Audio Visualization Comparison Runner
# This script runs the complete comparison analysis

echo "=========================================="
echo "Audio Visualization Comparison Tool"
echo "=========================================="
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "Please install Python 3 to continue"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo ""

# Check if we're in the right directory
if [ ! -f "src/audio_visualization_comparison.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

echo "Current directory: $(pwd)"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install requirements
echo "Installing/updating dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r src/requirements_comparison.txt
echo "✓ Dependencies installed"
echo ""

# Run comparison tool
echo "=========================================="
echo "Running Comparison Analysis..."
echo "=========================================="
echo ""

cd src
python3 audio_visualization_comparison.py

# Check if successful
if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ Comparison Complete!"
    echo "=========================================="
    echo ""
    echo "Generated files in ./comparison_output/:"
    ls -lh comparison_output/
    echo ""
    echo "📊 View the results:"
    echo "  - Open comparison_output/COMPARISON_REPORT.md"
    echo "  - View PNG files for visualizations"
    echo "  - Check comparison_matrix.csv for raw data"
    echo ""
    
    # Run Unity integration helper
    echo "Generating Unity integration guides..."
    python3 unity_integration_helper.py
    echo ""
    echo "📖 Unity Integration:"
    echo "  - Open comparison_output/UNITY_EDITOR_INTEGRATION.md"
    echo ""
else
    echo ""
    echo "❌ Error occurred during comparison"
    exit 1
fi

cd ..

# Deactivate virtual environment
deactivate

echo "=========================================="
echo "All done! 🎉"
echo "=========================================="
