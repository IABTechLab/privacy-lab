#!/bin/bash

# Privacy Lab API Startup Script

echo "================================"
echo "Privacy Lab API Server"
echo "================================"
echo ""

# Check if in correct directory
if [ ! -d "api" ]; then
    echo "Error: api directory not found"
    echo "Please run this script from the privacy-lab root directory"
    exit 1
fi

# Check if dependencies are installed
echo "Checking dependencies..."
python -c "import fastapi, uvicorn, opendp, pailliers, anjana" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Dependencies not found. Installing..."
    cd api && python -m pip install -r requirements.txt
    cd ..
fi

echo ""
echo "Starting API server on http://localhost:8000"
echo ""
echo "Available endpoints:"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Root: http://localhost:8000/"
echo "  - k-Anonymity: POST http://localhost:8000/api/k-anonymity"
echo "  - Differential Privacy: POST http://localhost:8000/api/differential-privacy"
echo "  - Homomorphic Encryption: POST http://localhost:8000/api/homomorphic-encryption"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd api && python main.py
