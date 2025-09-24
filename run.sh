#!/bin/bash

# Zulfi Web Chatbot - Run Script
# This script builds and runs both frontend and backend

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

# Function to cleanup background processes on exit
cleanup() {
    print_status "Shutting down services..."
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    print_success "Services stopped."
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo "🚀 Starting Zulfi Web Chatbot..."

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
    print_warning ".env file not found. Creating from template..."
    if [ -f ".env.template" ]; then
        cp .env.template .env
        print_warning "Please edit .env file with your API keys before running again."
        exit 1
    else
        print_error "No .env.template found. Please create .env file manually."
        exit 1
    fi
fi

# Build frontend
print_status "Building React frontend..."
cd frontend
npm run build
cd ..

# Start backend server in background
print_status "Starting FastAPI backend server on port 8000..."
python3.11 -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Check if backend is running
if ! curl -s http://localhost:8000/status > /dev/null; then
    print_error "Backend failed to start. Check the logs above."
    cleanup
fi

print_success "✅ Backend server started successfully!"

# Start frontend development server in background (optional)
print_status "Starting frontend development server on port 5173..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
sleep 3

print_success "🎉 Zulfi Web Chatbot is now running!"
echo ""
print_status "📱 Access your application:"
echo "  🌐 Production Mode (FastAPI serves both): http://localhost:8000"
echo "  🔧 Development Mode (Hot reload):         http://localhost:5173"
echo "  📚 API Documentation:                     http://localhost:8000/docs"
echo "  🔍 API Status:                            http://localhost:8000/status"
echo ""
print_status "💡 Tips:"
echo "  - Use Ctrl+C to stop all services"
echo "  - Check logs in the terminal for any errors"
echo "  - Edit .env file to configure your API keys"
echo ""

# Keep script running and show status
while true; do
    sleep 10
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        print_error "Backend process died unexpectedly"
        cleanup
    fi
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        print_error "Frontend process died unexpectedly"
        cleanup
    fi
done
