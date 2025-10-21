#!/bin/bash

# Privacy Lab Web Interface Startup Script

echo "================================"
echo "Privacy Lab Web Interface"
echo "================================"
echo ""

# Check if in correct directory
if [ ! -d "web" ]; then
    echo "Error: web directory not found"
    echo "Please run this script from the privacy-lab root directory"
    exit 1
fi

echo "Starting web server on http://localhost:8080"
echo ""
echo "Make sure the API server is running on http://localhost:8000"
echo "  (Run ./start_api.sh in another terminal)"
echo ""
echo "Open http://localhost:8080 in your browser"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd web && python -m http.server 8080
