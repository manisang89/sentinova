# Multi-Agent Customer Sentiment Watchdog

A comprehensive multi-agent system for monitoring customer sentiment across email and form channels using AI-powered sentiment analysis.

## 🎯 Overview

This system consists of multiple specialized agents that work together to:
- **Monitor** customer communications from emails and web forms
- **Analyze** sentiment using Google's Gemini AI
- **Store** data in Firebase for real-time access
- **Visualize** sentiment trends and alerts in a live dashboard

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Email Agent    │    │   Form Agent    │    │      Other      │
│   (IMAP)        │    │  (Webhooks)     │    │    Sources      │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼──────────────┐
                    │     Firebase Firestore     │
                    │    (Central Data Store)    │
                    └─────────────┬──────────────┘
                                 │
                    ┌─────────────▼──────────────┐
                    │   Processing Agent         │
                    │   (Gemini AI Analysis)     │
                    └─────────────┬──────────────┘
                                 │
                    ┌─────────────▼──────────────┐
                    │   Streamlit Dashboard      │
                    │   (Real-time Monitoring)   │
                    └────────────────────────────┘
```

## 🚀 Features

### Email Monitoring
- **IMAP Integration**: Monitors email inbox for new customer messages
- **Automatic Processing**: Extracts sender, subject, and message content
- **Error Handling**: Robust retry logic and connection management
- **Security**: Secure credential management via environment variables

### Form Integration
- **Webhook Endpoints**: Multiple endpoints for different form types
- **Validation**: Input validation and sanitization
- **Metadata Extraction**: Captures form submission metadata
- **API Documentation**: RESTful API with proper error responses

### Sentiment Analysis
- **Gemini AI**: Advanced sentiment analysis with confidence scoring
- **Text Processing**: Cleans and preprocesses text for better analysis
- **Keyword Extraction**: Identifies sentiment-driving keywords
- **Batch Processing**: Efficient processing with configurable intervals

### Real-time Dashboard
- **Live Updates**: Auto-refreshing dashboard with configurable intervals
- **Interactive Charts**: Plotly-powered visualizations
- **Alert System**: Automated alerts for high negative sentiment
- **Filtering**: Advanced filtering by time, sentiment, and source

## 📋 Prerequisites

- Python 3.9+
- Firebase project with Firestore enabled
- Google Gemini API key
- Email account with IMAP access (for email monitoring)
- Docker (optional, for containerized deployment)

## 🛠️ Installation

### 1. Clone and Setup

```bash
git clone <repository-url>
cd sentiment-watchdog
chmod +x setup.sh
./setup.sh
```

### 2. Configure Environment

```bash
cp .env.template .env
# Edit .env with your configuration
```

Required environment variables:
```env
# Firebase
FIREBASE_CREDENTIALS_PATH=serviceAccountKey.json
GEMINI_API_KEY=your_gemini_api_key

# Email (for email agent)
EMAIL_IMAP_SERVER=imap.gmail.com
EMAIL_ADDRESS=support@company.com
EMAIL_PASSWORD=your_app_password

# Application
APP_ID=senti108
```

### 3. Firebase Setup

1. Create a Firebase project at https://console.firebase.google.com/
2. Enable Firestore Database
3. Create a service account:
   - Go to Project Settings → Service Accounts
   - Click "Generate new private key"
   - Save as `serviceAccountKey.json` in the project root

### 4. Gemini API Setup

1. Get API key from https://makersuite.google.com/app/apikey
2. Add to your `.env` file

## 🚀 Usage

### Option 1: Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Services will be available at:
- **Dashboard**: http://localhost:8501
- **Form Webhooks**: http://localhost:5000/webhook/*
- **Health Check**: http://localhost:5000/health

### Option 2: Manual Startup

```bash
# Terminal 1: Email Agent
python email_agent.py your_app_id

# Terminal 2: Form Agent
python form_agent.py your_app_id 5000

# Terminal 3: Processing Agent
python processing_agent.py your_app_id

# Terminal 4: Dashboard
streamlit run dashboard.py
```

### Option 3: System Services

```bash
# Create and enable systemd services
sudo ./create_services.sh your_app_id

# Start services
sudo systemctl start sentiment-email-agent
sudo systemctl start sentiment-form-agent
sudo systemctl start sentiment-processing-agent
sudo systemctl start sentiment-dashboard

# Check status
sudo systemctl status sentiment-*
```

## 📡 API Endpoints

### Form Webhooks

#### Contact Form
```bash
POST /webhook/contact-form
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "subject": "Need Help",
  "message": "I'm having trouble with my account..."
}
```

#### Feedback Form
```bash
POST /webhook/feedback
Content-Type: application/json

{
  "email": "customer@example.com",
  "rating": 2,
  "message": "The service was disappointing..."
}
```

#### Support Ticket
```bash
POST /webhook/support
Content-Type: application/json

{
  "name": "Jane Smith",
  "email": "jane@example.com",
  "priority": "high",
  "category": "technical",
  "message": "My application keeps crashing..."
}
```

#### Custom Form
```bash
POST /webhook/custom
Content-Type: application/json

{
  "custom_field": "value",
  "message": "Any message content...",
  "additional_data": "..."
}
```

### Health Check
```bash
GET /health

Response:
{
  "status": "healthy",
  "agent": "FormIngestionAgent",
  "app_id": "your_app_id",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 📊 Dashboard Features

### Main Views
- **System Overview**: Total tickets, processing status, error rates
- **Sentiment Analysis**: Distribution of anger, confusion, delight, neutral
- **Trend Charts**: Time-series visualization of sentiment patterns
- **Alert System**: Real-time alerts for high negative sentiment
- **Recent Messages**: Latest analyzed messages with details

### Filters
- **Time Range**: Last 24 hours, 3 days, week, month
- **Sentiment Type**: Filter by specific sentiment categories
- **Source Channel**: Filter by email, forms, etc.

### Auto-refresh
- Configurable refresh intervals (30s, 1m, 2m, 5m)
- Manual refresh option
- Real-time data updates

## 🔧 Configuration

### Processing Agent Settings
```env
PROCESSING_BATCH_SIZE=10        # Messages processed per batch
PROCESSING_INTERVAL=60          # Seconds between processing cycles
MAX_RETRIES=3                   # Retry attempts for failed processing
```

### Email Agent Settings
```env
EMAIL_CHECK_INTERVAL=300        # Seconds between email checks
EMAIL_IMAP_SERVER=imap.gmail.com
EMAIL_PORT=993                  # IMAP SSL port
```

### Form Agent Settings
```env
FORM_AGENT_PORT=5000           # Webhook server port
FORM_VALIDATION_STRICT=true    # Enable strict validation
```

## 🔍 Monitoring & Troubleshooting

### Logs
All agents write logs to:
- Console output
- Log files: `{agent_name}_{app_id}.log`

### Common Issues

#### Firebase Connection Errors
```bash
# Check credentials
ls -la serviceAccountKey.json

# Verify Firebase project ID in credentials
cat serviceAccountKey.json | grep project_id
```

#### Email Authentication Errors
```bash
# For Gmail, use App Passwords:
# 1. Enable 2FA on your Google account
# 2. Generate App Password
# 3. Use App Password instead of regular password
```

#### Gemini API Errors
```bash
# Check API key validity
curl -H "Authorization: Bearer $GEMINI_API_KEY" \
     "https://generativelanguage.googleapis.com/v1beta/models"
```

### Performance Monitoring

Monitor system performance:
```bash
# Docker stats
docker stats

# System resources
htop

# Log analysis
tail -f *.log | grep ERROR
```

## 🔐 Security Considerations

### API Keys
- Store all keys in environment variables
- Never commit credentials to version control
- Use Firebase security rules to restrict access
- Rotate API keys regularly

### Network Security
- Use HTTPS for webhook endpoints in production
- Implement rate limiting on webhook endpoints
- Validate and sanitize all input data
- Monitor for suspicious activity

### Data Privacy
- Implement data retention policies
- Encrypt sensitive data at rest
- Use Firebase security rules for access control
- Comply with relevant privacy regulations

## 📈 Scaling

### Horizontal Scaling
- Run multiple processing agents with different APP_IDs
- Use load balancer for form agents
- Implement message queuing for high volume

### Vertical Scaling
- Increase PROCESSING_BATCH_SIZE for faster processing
- Optimize Firebase queries with indexes
- Use Firebase caching for dashboard performance

### High Availability
- Deploy across multiple regions
- Use Firebase backup and restore
- Implement health checks and automatic restarts
- Monitor system metrics and alerts

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the troubleshooting section above
- Review log files for error details
- Open an issue on GitHub
- Contact the development team

## 🔄 Version History

- **v1.0.0**: Initial release with basic sentiment analysis
- **v1.1.0**: Added form webhook support
- **v1.2.0**: Enhanced dashboard with real-time alerts
- **v1.3.0**: Docker containerization and deployment automation

---

**Built with ❤️ for better customer experience monitoring**
