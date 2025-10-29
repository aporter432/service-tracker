#!/bin/bash
# Setup script for ORBCOMM Service Tracker
# Automates initial setup and configuration

set -e

echo "🚀 ORBCOMM Service Tracker - Setup Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "📌 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo -e "${RED}❌ Python $required_version or higher required. Found: $python_version${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python $python_version${NC}"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠️  Virtual environment already exists${NC}"
fi
echo ""

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip --quiet
echo -e "${GREEN}✅ pip upgraded${NC}"
echo ""

# Install dependencies
echo "📥 Installing dependencies..."
if [ "$1" == "--production" ]; then
    echo "Installing production dependencies..."
    pip install -r requirements-prod.txt --quiet
else
    echo "Installing base dependencies..."
    pip install -r requirements.txt --quiet
fi
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Create data directory
echo "📁 Creating data directory..."
ORBCOMM_DATA_DIR="${HOME}/.orbcomm"
mkdir -p "$ORBCOMM_DATA_DIR"
mkdir -p "$ORBCOMM_DATA_DIR/logs"
mkdir -p "$ORBCOMM_DATA_DIR/inbox1"
mkdir -p "$ORBCOMM_DATA_DIR/inbox2"
echo -e "${GREEN}✅ Data directory created at $ORBCOMM_DATA_DIR${NC}"
echo ""

# Create .env file
echo "⚙️  Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env

    # Generate secret key
    secret_key=$(python3 -c "import secrets; print(secrets.token_hex(32))")

    # Update .env with generated values
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|SECRET_KEY=.*|SECRET_KEY=$secret_key|" .env
        sed -i '' "s|ORBCOMM_DATA_DIR=.*|ORBCOMM_DATA_DIR=$ORBCOMM_DATA_DIR|" .env
        sed -i '' "s|DATABASE_PATH=.*|DATABASE_PATH=$ORBCOMM_DATA_DIR/tracker.db|" .env
        sed -i '' "s|LOG_DIR=.*|LOG_DIR=$ORBCOMM_DATA_DIR/logs|" .env
    else
        # Linux
        sed -i "s|SECRET_KEY=.*|SECRET_KEY=$secret_key|" .env
        sed -i "s|ORBCOMM_DATA_DIR=.*|ORBCOMM_DATA_DIR=$ORBCOMM_DATA_DIR|" .env
        sed -i "s|DATABASE_PATH=.*|DATABASE_PATH=$ORBCOMM_DATA_DIR/tracker.db|" .env
        sed -i "s|LOG_DIR=.*|LOG_DIR=$ORBCOMM_DATA_DIR/logs|" .env
    fi

    echo -e "${GREEN}✅ .env file created with generated secret key${NC}"
else
    echo -e "${YELLOW}⚠️  .env file already exists (skipping)${NC}"
fi
echo ""

# Initialize database
echo "🗄️  Initializing database..."
python3 -c "from orbcomm_tracker.database import Database; db = Database(); db.create_tables(); print('✅ Database initialized')"
echo ""

# Check for credentials
echo "🔑 Checking Gmail API credentials..."
if [ ! -f "$ORBCOMM_DATA_DIR/credentials.json" ]; then
    echo -e "${YELLOW}⚠️  Gmail credentials not found${NC}"
    echo "   Please follow these steps:"
    echo "   1. Go to https://console.cloud.google.com/"
    echo "   2. Create OAuth 2.0 credentials"
    echo "   3. Download and save as: $ORBCOMM_DATA_DIR/credentials.json"
    echo "   4. Run: python3 setup_gmail_auth.py --inbox 1"
else
    echo -e "${GREEN}✅ Gmail credentials found${NC}"
fi
echo ""

# Run tests
if [ "$1" != "--skip-tests" ]; then
    echo "🧪 Running tests..."
    python3 -m pytest tests/ -v || echo -e "${YELLOW}⚠️  Some tests failed${NC}"
    echo ""
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✨ Setup complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Configure Gmail API credentials (if not done)"
echo "3. Run dashboard: python3 orbcomm_dashboard.py"
echo "4. Access at: http://localhost:5000"
echo ""
echo "For production deployment, see: DEPLOYMENT.md"
echo ""
