#!/bin/bash

# Multi-Agent Sentiment Watchdog Setup Script

echo "Setting up Multi-Agent Sentiment Watchdog System..."

# Create project directory structure
mkdir -p logs
mkdir -p config
mkdir -p docs

# Check for required files
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.template .env
    echo "⚠️  Please edit .env file with your configuration!"
fi

if [ ! -f "serviceAccountKey.json" ]; then
    echo "⚠️  Please add your Firebase serviceAccountKey.json file!"
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create systemd service files (optional)
read -p "Do you want to create systemd service files? (y/n): " create_services

if [ "$create_services" = "y" ]; then
    sudo bash create_services.sh
fi

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Add your Firebase serviceAccountKey.json file"
echo "3. Run the agents:"
echo "   - Email agent: python email_agent.py your_app_id"
echo "   - Form agent: python form_agent.py your_app_id"
echo "   - Processing agent: python processing_agent.py your_app_id"
echo "   - Dashboard: streamlit run dashboard.py"
echo ""
echo "Or use Docker Compose:"
echo "   docker-compose up -d"
