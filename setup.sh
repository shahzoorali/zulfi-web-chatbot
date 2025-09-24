#!/bin/bash

# Zulfi Web Chatbot - Complete Setup Script for Fresh Ubuntu
# This script installs everything needed to run the chatbot from scratch

set -e  # Exit on any error

echo "🚀 Starting Zulfi Web Chatbot Setup on Fresh Ubuntu..."

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

# Update system packages
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install essential build tools
print_status "Installing essential build tools..."
sudo apt install -y curl wget git build-essential software-properties-common apt-transport-https ca-certificates gnupg lsb-release

# Install Node.js 18.x
print_status "Installing Node.js 18.x..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Verify Node.js installation
print_status "Verifying Node.js installation..."
node --version
npm --version

# Install Python 3.11
print_status "Installing Python 3.11..."
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Install pip for Python 3.11
print_status "Installing pip for Python 3.11..."
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
sudo python3.11 get-pip.py
rm get-pip.py

# Verify Python installation
print_status "Verifying Python installation..."
python3.11 --version
pip3.11 --version

# Install system dependencies for Python packages
print_status "Installing system dependencies for Python packages..."
sudo apt install -y gcc g++ libffi-dev libssl-dev libxml2-dev libxslt1-dev zlib1g-dev libjpeg-dev libpng-dev

# Clone the repository (if not already present)
if [ ! -d "zulfi-web-chatbot" ]; then
    print_status "Cloning repository..."
    git clone https://github.com/shahzoorali/zulfi-web-chatbot.git
fi

cd zulfi-web-chatbot

# Create Python virtual environment
print_status "Creating Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip in virtual environment
print_status "Upgrading pip in virtual environment..."
pip install --upgrade pip

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt

# Install Playwright browsers
print_status "Installing Playwright browsers..."
playwright install chromium

# Install Node.js dependencies for frontend
print_status "Installing Node.js dependencies..."
cd frontend
npm install
cd ..

# Create environment file template
print_status "Creating environment file template..."
cat > .env.template << 'EOF'
# IBM Watson Configuration
IBM_API_KEY=your_ibm_api_key_here
WATSONX_PROJECT_ID=your_watson_project_id_here

# Astra DB Configuration  
ASTRA_DEVOPS_TOKEN=your_astra_devops_token_here
ASTRA_DB_APPLICATION_TOKEN=your_astra_db_token_here

# Optional API Key (leave empty if not using)
API_KEY=
EOF

# Make run script executable
chmod +x run.sh

print_success "✅ Setup completed successfully!"
print_warning "⚠️  Please configure your environment variables:"
print_status "1. Copy .env.template to .env"
print_status "2. Edit .env with your actual API keys"
print_status "3. Run ./run.sh to start the application"

echo ""
print_status "Next steps:"
echo "  cp .env.template .env"
echo "  nano .env  # Edit with your API keys"
echo "  ./run.sh   # Start the application"
