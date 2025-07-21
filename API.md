# API Documentation

## Form Ingestion Webhooks

### Base URL
```
http://localhost:5000
```

### Authentication
Currently, no authentication is required for webhook endpoints. In production, implement proper authentication.

### Common Response Format

#### Success Response
```json
{
  "status": "success",
  "message": "Description of successful operation",
  "submission_id": "generated_document_id"
}
```

#### Error Response
```json
{
  "error": "Error type",
  "message": "Detailed error description"
}
```

### Endpoints

#### Health Check
Check if the form agent is running and healthy.

**Request:**
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "agent": "FormIngestionAgent",
  "app_id": "your_app_id",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

#### Contact Form Webhook
Process contact form submissions.

**Request:**
```http
POST /webhook/contact-form
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "company": "Acme Corp",
  "subject": "Need assistance",
  "message": "I need help with my account setup..."
}
```

**Required Fields:**
- `message`: The main message content (max 10,000 characters)

**Optional Fields:**
- `name`: Contact person's name
- `email`: Contact email address
- `phone`: Contact phone number
- `company`: Company name
- `subject`: Message subject

**Response:**
```json
{
  "status": "success",
  "message": "Contact form submitted successfully",
  "submission_id": "abc123def456"
}
```

#### Feedback Webhook
Process customer feedback submissions.

**Request:**
```http
POST /webhook/feedback
Content-Type: application/json

{
  "email": "customer@example.com",
  "rating": 2,
  "category": "service",
  "message": "The service was slow and unhelpful..."
}
```

**Required Fields:**
- `message`: Feedback content (max 10,000 characters)

**Optional Fields:**
- `email`: Customer email
- `rating`: Numeric rating (1-5)
- `category`: Feedback category
- `name`: Customer name

#### Support Ticket Webhook
Process support ticket submissions.

**Request:**
```http
POST /webhook/support
Content-Type: application/json

{
  "name": "Jane Smith",
  "email": "jane@example.com",
  "priority": "high",
  "category": "technical",
  "product": "Pro Plan",
  "message": "My application keeps crashing when I try to export data..."
}
```

**Required Fields:**
- `message`: Support issue description (max 10,000 characters)

**Optional Fields:**
- `name`: Customer name
- `email`: Customer email
- `priority`: Issue priority (low, medium, high, urgent)
- `category`: Issue category (technical, billing, feature, etc.)
- `product`: Product or service affected

#### Custom Form Webhook
Process any custom form submissions.

**Request:**
```http
POST /webhook/custom
Content-Type: application/json

{
  "custom_field_1": "value1",
  "custom_field_2": "value2",
  "message": "Custom message content...",
  "metadata": {
    "form_version": "2.1",
    "source_page": "/contact-us"
  }
}
```

**Required Fields:**
- `message`: Message content (max 10,000 characters)

**Optional Fields:**
- Any additional fields as needed by your forms

### Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid input data |
| 500 | Internal Server Error |

### Rate Limiting
Currently no rate limiting is implemented. Consider implementing rate limiting for production use.

### Data Processing Flow

1. **Validation**: Input data is validated for required fields and data types
2. **Sanitization**: Message content is cleaned and validated for length
3. **Metadata Extraction**: Form submission metadata is captured (IP, user agent, etc.)
4. **Storage**: Data is stored in Firebase Firestore with timestamp
5. **Processing**: Background agent picks up new submissions for sentiment analysis

### Integration Examples

#### JavaScript/jQuery
```javascript
// Contact form submission
$.ajax({
    url: 'http://localhost:5000/webhook/contact-form',
    method: 'POST',
    contentType: 'application/json',
    data: JSON.stringify({
        name: $('#name').val(),
        email: $('#email').val(),
        subject: $('#subject').val(),
        message: $('#message').val()
    }),
    success: function(response) {
        console.log('Form submitted successfully:', response);
        // Show success message to user
    },
    error: function(xhr, status, error) {
        console.error('Form submission failed:', error);
        // Show error message to user
    }
});
```

#### Python
```python
import requests

# Submit feedback
response = requests.post(
    'http://localhost:5000/webhook/feedback',
    json={
        'email': 'customer@example.com',
        'rating': 3,
        'message': 'The product is good but could be improved'
    }
)

if response.status_code == 200:
    print('Feedback submitted:', response.json())
else:
    print('Error:', response.text)
```

#### cURL
```bash
# Submit support ticket
curl -X POST http://localhost:5000/webhook/support \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "priority": "high",
    "message": "Need urgent help with billing issue"
  }'
```

### Security Notes

1. **Input Validation**: All inputs are validated and sanitized
2. **Content-Type**: Only `application/json` content type is accepted
3. **Message Length**: Messages are limited to 10,000 characters
4. **XSS Prevention**: HTML content is not processed, only plain text
5. **Rate Limiting**: Consider implementing rate limiting for production

### Production Deployment

For production deployment:

1. **Use HTTPS**: Always use HTTPS for webhook endpoints
2. **Authentication**: Implement webhook authentication (tokens, signatures)
3. **Rate Limiting**: Add rate limiting to prevent abuse
4. **Monitoring**: Monitor webhook performance and error rates
5. **Logging**: Implement comprehensive logging for debugging
6. **Load Balancing**: Use load balancer for high availability
