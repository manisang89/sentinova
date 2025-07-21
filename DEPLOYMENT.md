# Deployment Guide

## Production Deployment Options

### 1. Docker Compose Deployment (Recommended)

#### Prerequisites
- Docker and Docker Compose installed
- Domain name and SSL certificate
- Firebase project configured
- Gemini API key

#### Step-by-Step Process

1. **Clone and Configure**
```bash
git clone <repository-url>
cd sentiment-watchdog
cp .env.template .env
# Edit .env with production values
```

2. **Add SSL Configuration**
Create `nginx.conf`:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/ssl/certs/your-cert.pem;
    ssl_certificate_key /etc/ssl/private/your-key.key;

    location / {
        proxy_pass http://dashboard:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /webhook/ {
        proxy_pass http://form-agent:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

3. **Update Docker Compose for Production**
Create `docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - /etc/ssl:/etc/ssl:ro
    depends_on:
      - dashboard
      - form-agent

  email-agent:
    build: .
    dockerfile: Dockerfile.email
    environment:
      - APP_ID=${APP_ID}
    env_file:
      - .env
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs

  form-agent:
    build: .
    dockerfile: Dockerfile.form
    environment:
      - APP_ID=${APP_ID}
    env_file:
      - .env
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs

  processing-agent:
    build: .
    dockerfile: Dockerfile.processing
    environment:
      - APP_ID=${APP_ID}
    env_file:
      - .env
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs

  dashboard:
    build: .
    dockerfile: Dockerfile.dashboard
    environment:
      - APP_ID=${APP_ID}
    env_file:
      - .env
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs

volumes:
  logs:
```

4. **Deploy**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 2. Cloud Platform Deployment

#### Google Cloud Platform (GCP)

1. **Cloud Run Deployment**
```bash
# Build and push images
gcloud builds submit --tag gcr.io/$PROJECT_ID/sentiment-dashboard
gcloud builds submit --tag gcr.io/$PROJECT_ID/sentiment-form-agent
gcloud builds submit --tag gcr.io/$PROJECT_ID/sentiment-processing-agent

# Deploy services
gcloud run deploy sentiment-dashboard \
  --image gcr.io/$PROJECT_ID/sentiment-dashboard \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

gcloud run deploy sentiment-form-agent \
  --image gcr.io/$PROJECT_ID/sentiment-form-agent \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

# Deploy processing agent on Cloud Functions or Compute Engine
```

2. **Kubernetes Deployment**
Create `k8s-deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sentiment-dashboard
spec:
  replicas: 2
  selector:
    matchLabels:
      app: sentiment-dashboard
  template:
    metadata:
      labels:
        app: sentiment-dashboard
    spec:
      containers:
      - name: dashboard
        image: gcr.io/PROJECT_ID/sentiment-dashboard
        ports:
        - containerPort: 8501
        env:
        - name: APP_ID
          value: "production"
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: sentiment-secrets
              key: gemini-api-key

---
apiVersion: v1
kind: Service
metadata:
  name: sentiment-dashboard-service
spec:
  selector:
    app: sentiment-dashboard
  ports:
  - port: 80
    targetPort: 8501
  type: LoadBalancer
```

#### AWS Deployment

1. **ECS Fargate**
```json
{
  "family": "sentiment-watchdog",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "dashboard",
      "image": "your-ecr-repo/sentiment-dashboard:latest",
      "portMappings": [
        {
          "containerPort": 8501,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "APP_ID",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "GEMINI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:sentiment-secrets"
        }
      ]
    }
  ]
}
```

### 3. VPS Deployment

#### Ubuntu Server Setup

1. **Server Preparation**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.12.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create deployment user
sudo useradd -m -s /bin/bash sentiment
sudo usermod -aG docker sentiment
```

2. **Application Deployment**
```bash
# Switch to deployment user
sudo su - sentiment

# Clone repository
git clone <repository-url>
cd sentiment-watchdog

# Configure environment
cp .env.template .env
nano .env  # Edit with production values

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

3. **Set up Reverse Proxy (Nginx)**
```bash
sudo apt install nginx certbot python3-certbot-nginx

# Configure Nginx
sudo nano /etc/nginx/sites-available/sentiment-watchdog

# Enable site
sudo ln -s /etc/nginx/sites-available/sentiment-watchdog /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

## Environment Configuration

### Production Environment Variables

```env
# Firebase Configuration
FIREBASE_CREDENTIALS_JSON={"type": "service_account", ...}
# OR
FIREBASE_CREDENTIALS_PATH=/app/secrets/serviceAccountKey.json

# Gemini API
GEMINI_API_KEY=your_production_api_key

# Email Configuration
EMAIL_IMAP_SERVER=imap.gmail.com
EMAIL_ADDRESS=support@yourcompany.com
EMAIL_PASSWORD=your_app_password

# Processing Configuration
PROCESSING_BATCH_SIZE=20
PROCESSING_INTERVAL=30
MAX_RETRIES=5

# Application Configuration
APP_ID=production
LOG_LEVEL=INFO

# Security
ALLOWED_ORIGINS=https://yourapp.com,https://www.yourapp.com
WEBHOOK_SECRET=your_webhook_secret
```

### Secrets Management

#### Using Docker Secrets
```bash
# Create secrets
echo "your_gemini_api_key" | docker secret create gemini_api_key -
echo "your_firebase_json" | docker secret create firebase_credentials -

# Update docker-compose.yml
version: '3.8'
services:
  processing-agent:
    secrets:
      - gemini_api_key
      - firebase_credentials
    environment:
      - GEMINI_API_KEY_FILE=/run/secrets/gemini_api_key
      - FIREBASE_CREDENTIALS_FILE=/run/secrets/firebase_credentials

secrets:
  gemini_api_key:
    external: true
  firebase_credentials:
    external: true
```

#### Using Kubernetes Secrets
```bash
# Create secrets
kubectl create secret generic sentiment-secrets \
  --from-literal=gemini-api-key=your_api_key \
  --from-file=firebase-credentials=serviceAccountKey.json

# Reference in deployment
env:
- name: GEMINI_API_KEY
  valueFrom:
    secretKeyRef:
      name: sentiment-secrets
      key: gemini-api-key
```

## Monitoring and Maintenance

### Health Checks

1. **Application Health**
```bash
# Check form agent
curl http://localhost:5000/health

# Check dashboard
curl http://localhost:8501/

# Check containers
docker ps
docker logs sentiment-watchdog_processing-agent_1
```

2. **Automated Monitoring**
```bash
# Create monitoring script
cat > /opt/sentiment-watchdog/monitor.sh << 'EOF'
#!/bin/bash

# Check services
services=("email-agent" "form-agent" "processing-agent" "dashboard")

for service in "${services[@]}"; do
    if ! docker ps | grep -q "sentiment-watchdog_${service}"; then
        echo "Service $service is down!" | mail -s "Alert: $service down" admin@yourcompany.com
        docker-compose restart $service
    fi
done

# Check disk space
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "Disk usage is ${DISK_USAGE}%" | mail -s "Alert: High disk usage" admin@yourcompany.com
fi
EOF

chmod +x /opt/sentiment-watchdog/monitor.sh

# Add to crontab
echo "*/5 * * * * /opt/sentiment-watchdog/monitor.sh" | crontab -
```

### Log Management

1. **Log Rotation**
```bash
# Configure logrotate
sudo cat > /etc/logrotate.d/sentiment-watchdog << 'EOF'
/opt/sentiment-watchdog/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 sentiment sentiment
    postrotate
        docker-compose -f /opt/sentiment-watchdog/docker-compose.prod.yml restart
    endscript
}
EOF
```

2. **Centralized Logging**
```yaml
# Add to docker-compose.yml
version: '3.8'
services:
  processing-agent:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        labels: "service=processing-agent"
```

### Backup Strategy

1. **Firebase Backup**
```bash
# Automated Firestore backup
gcloud firestore export gs://your-backup-bucket/$(date +%Y%m%d)
```

2. **Configuration Backup**
```bash
# Backup script
cat > /opt/sentiment-watchdog/backup.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/backup/sentiment-watchdog/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Backup configuration
cp -r /opt/sentiment-watchdog/.env $BACKUP_DIR/
cp -r /opt/sentiment-watchdog/docker-compose.prod.yml $BACKUP_DIR/

# Backup logs
tar -czf $BACKUP_DIR/logs.tar.gz /opt/sentiment-watchdog/logs/

# Upload to cloud storage (optional)
# aws s3 sync $BACKUP_DIR s3://your-backup-bucket/
EOF
```

## Scaling Considerations

### Horizontal Scaling

1. **Multiple Processing Agents**
```yaml
# Scale processing agents
processing-agent:
  deploy:
    replicas: 3
  environment:
    - WORKER_ID=${HOSTNAME}
```

2. **Load Balancing Form Agents**
```yaml
# Nginx upstream configuration
upstream form_agents {
    server form-agent-1:5000;
    server form-agent-2:5000;
    server form-agent-3:5000;
}

server {
    location /webhook/ {
        proxy_pass http://form_agents;
    }
}
```

### Performance Optimization

1. **Database Indexing**
```javascript
// Create Firestore indexes
db.collection('artifacts/production/public/data/raw_tickets')
  .createIndex({status: 1, timestamp: -1});
```

2. **Caching**
```python
# Add Redis caching
import redis
r = redis.Redis(host='redis', port=6379, db=0)

# Cache processed results
@cached(cache=TTLCache(maxsize=1000, ttl=300))
def get_sentiment_stats():
    # Implementation
    pass
```

## Security Hardening

### Network Security

1. **Firewall Configuration**
```bash
# UFW configuration
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

2. **SSL/TLS Configuration**
```nginx
# Strong SSL configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
add_header Strict-Transport-Security "max-age=63072000";
```

### Application Security

1. **Input Validation**
```python
# Enhanced input validation
from cerberus import Validator

schema = {
    'message': {
        'type': 'string',
        'maxlength': 10000,
        'required': True,
        'regex': '^[a-zA-Z0-9\s\.,!?-]*$'
    }
}

validator = Validator(schema)
```

2. **Rate Limiting**
```python
# Flask-Limiter implementation
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)

@app.route('/webhook/contact-form', methods=['POST'])
@limiter.limit("10 per minute")
def contact_form_webhook():
    # Implementation
    pass
```

## Troubleshooting

### Common Issues

1. **Firebase Connection Timeout**
```bash
# Check network connectivity
curl -I https://firestore.googleapis.com

# Verify credentials
python3 -c "
import firebase_admin
from firebase_admin import credentials
cred = credentials.Certificate('serviceAccountKey.json')
print('Credentials valid')
"
```

2. **Gemini API Rate Limits**
```python
# Implement exponential backoff
import time
import random

def retry_with_backoff(func, max_retries=5):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait_time)
```

3. **High Memory Usage**
```bash
# Monitor memory usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Optimize processing batch size
export PROCESSING_BATCH_SIZE=5
```

### Performance Monitoring

1. **Metrics Collection**
```python
# Add Prometheus metrics
from prometheus_client import Counter, Histogram, start_http_server

message_counter = Counter('messages_processed_total', 'Total processed messages')
processing_time = Histogram('processing_duration_seconds', 'Time spent processing')

# Start metrics server
start_http_server(8000)
```

2. **Alerting**
```yaml
# Prometheus alerting rules
groups:
- name: sentiment-watchdog
  rules:
  - alert: HighErrorRate
    expr: rate(messages_failed_total[5m]) > 0.1
    for: 2m
    annotations:
      summary: "High error rate in sentiment processing"
```

This deployment guide provides comprehensive instructions for deploying the sentiment watchdog system in various environments with proper security, monitoring, and scaling considerations.
