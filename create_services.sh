#!/bin/bash

# Create systemd service files for the agents

APP_ID=${1:-"default"}
WORK_DIR=$(pwd)
USER=$(whoami)

# Email Agent Service
cat > /etc/systemd/system/sentiment-email-agent.service << EOF
[Unit]
Description=Sentiment Watchdog Email Agent
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$WORK_DIR
Environment=PATH=$WORK_DIR/.venv/bin
ExecStart=$WORK_DIR/.venv/bin/python $WORK_DIR/email_agent.py $APP_ID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Form Agent Service
cat > /etc/systemd/system/sentiment-form-agent.service << EOF
[Unit]
Description=Sentiment Watchdog Form Agent
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$WORK_DIR
Environment=PATH=$WORK_DIR/.venv/bin
ExecStart=$WORK_DIR/.venv/bin/python $WORK_DIR/form_agent.py $APP_ID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Processing Agent Service
cat > /etc/systemd/system/sentiment-processing-agent.service << EOF
[Unit]
Description=Sentiment Watchdog Processing Agent
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$WORK_DIR
Environment=PATH=$WORK_DIR/.venv/bin
ExecStart=$WORK_DIR/.venv/bin/python $WORK_DIR/processing_agent.py $APP_ID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Dashboard Service
cat > /etc/systemd/system/sentiment-dashboard.service << EOF
[Unit]
Description=Sentiment Watchdog Dashboard
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$WORK_DIR
Environment=PATH=$WORK_DIR/.venv/bin
ExecStart=$WORK_DIR/.venv/bin/streamlit run $WORK_DIR/dashboard.py --server.port=8501 --server.address=0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable services
systemctl daemon-reload
systemctl enable sentiment-email-agent
systemctl enable sentiment-form-agent
systemctl enable sentiment-processing-agent
systemctl enable sentiment-dashboard

echo "✅ Systemd services created and enabled!"
echo "Start services with:"
echo "  sudo systemctl start sentiment-email-agent"
echo "  sudo systemctl start sentiment-form-agent"
echo "  sudo systemctl start sentiment-processing-agent"
echo "  sudo systemctl start sentiment-dashboard"
