#!/bin/bash

# Zulfi Web Chatbot - Production Deployment Script
# This script runs the chatbot in production mode (backend serves frontend)

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to cleanup on exit
cleanup() {
    print_status "Shutting down production server..."
    if [ ! -z "$SERVER_PID" ]; then
        kill $SERVER_PID 2>/dev/null || true
    fi
    print_success "Production server stopped."
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo "🚀 Starting Zulfi Web Chatbot in Production Mode..."

# Check if we're in the right directory
if [ ! -f "server.py" ] || [ ! -d "frontend" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_error "Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
print_status "Activating Python virtual environment..."
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found. Please create it with your API keys."
    exit 1
fi

# Build frontend
print_status "Building React frontend for production..."
cd frontend
npm run build
cd ..

# Start production server
print_status "Starting production server on port 8000..."
python3.11 -m uvicorn server:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!

# Wait for server to start
sleep 3

# Check if server is running
if ! curl -s http://localhost:8000/status > /dev/null; then
    print_error "Server failed to start. Check the logs above."
    cleanup
fi

print_success "🎉 Zulfi Web Chatbot is now running in production mode!"
echo ""
print_status "📱 Access your application:"
echo "  🌐 Web Application:     http://localhost:8000"
echo "  📚 API Documentation:   http://localhost:8000/docs"
echo "  🔍 API Status:          http://localhost:8000/status"
echo ""
print_status "💡 Tips:"
echo "  - Use Ctrl+C to stop the server"
echo "  - The server serves both API and frontend"
echo "  - Check logs in the terminal for any errors"
echo ""

# Keep script running and show status
while true; do
    sleep 10
    if ! kill -0 $SERVER_PID 2>/dev/null; then
        print_error "Server process died unexpectedly"
        cleanup
    fi
done