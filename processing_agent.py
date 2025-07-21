"""
Sentiment Analysis & Processing Agent for Multi-Agent Sentiment Watchdog System
Processes raw customer messages using Gemini API for sentiment analysis
"""

import time
import logging
from datetime import datetime, timedelta
from firebase_admin import firestore
from firebase_admin import credentials
import firebase_admin
import os
from dotenv import load_dotenv
import json
import google.generativeai as genai
from retrying import retry
import signal
import sys
from typing import Dict, List, Optional
import re

# Load environment variables
load_dotenv()

class SentimentProcessingAgent:
    def __init__(self, app_id):
        self.app_id = app_id
        self.setup_logging()
        self.init_firebase()
        self.init_gemini()
        self.running = True

        # Processing configuration
        self.batch_size = int(os.getenv('PROCESSING_BATCH_SIZE', '10'))
        self.processing_interval = int(os.getenv('PROCESSING_INTERVAL', '60'))
        self.max_retries = int(os.getenv('MAX_RETRIES', '3'))

    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'processing_agent_{self.app_id}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(f'ProcessingAgent_{self.app_id}')

    def init_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if Firebase app is already initialized
            firebase_admin.get_app()
        except ValueError:
            # Initialize Firebase if not already done
            cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH', 'serviceAccountKey.json')
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            else:
                # Use environment variable for credentials
                cred_json = os.getenv('FIREBASE_CREDENTIALS_JSON')
                if cred_json:
                    cred_dict = json.loads(cred_json)
                    cred = credentials.Certificate(cred_dict)
                    firebase_admin.initialize_app(cred)
                else:
                    raise ValueError("Firebase credentials not found")

        self.db = firestore.client()
        self.logger.info("Firebase initialized successfully")

    def init_gemini(self):
        """Initialize Gemini API"""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.logger.info("Gemini API initialized successfully")

    def clean_text(self, text: str) -> str:
        """Clean and prepare text for analysis"""
        if not text:
            return ""

        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text.strip())

        # Remove email headers and signatures
        text = re.sub(r'^(From:|To:|Subject:|Date:).*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^--.*$', '', text, flags=re.MULTILINE)

        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)

        # Remove excessive punctuation
        text = re.sub(r'[.]{3,}', '...', text)
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)

        return text.strip()

    @retry(stop_max_attempt_number=3, wait_exponential_multiplier=1000)
    def analyze_sentiment_with_gemini(self, message: str) -> Dict:
        """Analyze sentiment using Gemini API with retry logic"""
        try:
            cleaned_message = self.clean_text(message)

            if len(cleaned_message) < 10:
                return {
                    'sentiment': 'neutral',
                    'summary': 'Message too short for analysis',
                    'confidence': 0.5,
                    'keywords': []
                }

            prompt = f"""Analyze the sentiment of the following customer support message. Categorize the sentiment as one of: 'anger', 'confusion', 'delight', or 'neutral'. 

Provide a confidence score (0.0 to 1.0), a brief summary of the core issue or feeling expressed, and extract key keywords that indicate the sentiment.

Respond in JSON format with these exact keys:
- "sentiment": one of "anger", "confusion", "delight", or "neutral"
- "summary": brief summary of the issue/feeling (max 100 characters)
- "confidence": confidence score between 0.0 and 1.0
- "keywords": array of relevant keywords (max 5 keywords)

Examples:
Input: "My internet has been down for 3 days! This is unacceptable, I need it fixed NOW!"
Output: {{"sentiment": "anger", "summary": "Customer frustrated by 3-day internet outage", "confidence": 0.95, "keywords": ["frustrated", "outage", "unacceptable", "down", "fix"]}}

Input: "Thank you so much for the quick resolution! The team was amazing and very helpful."
Output: {{"sentiment": "delight", "summary": "Customer pleased with quick and helpful service", "confidence": 0.9, "keywords": ["thank you", "quick", "amazing", "helpful", "resolution"]}}

Input: "I'm not sure how to set up my new router. Can someone help me understand the process?"
Output: {{"sentiment": "confusion", "summary": "Customer needs help with router setup", "confidence": 0.8, "keywords": ["not sure", "help", "router", "setup", "understand"]}}

Message to analyze:
{cleaned_message}"""

            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=500
                )
            )

            if not response.text:
                raise Exception("Empty response from Gemini API")

            # Clean the response text
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]

            # Parse JSON response
            result = json.loads(response_text)

            # Validate response format
            required_keys = ['sentiment', 'summary', 'confidence', 'keywords']
            for key in required_keys:
                if key not in result:
                    raise ValueError(f"Missing required key: {key}")

            # Validate sentiment value
            valid_sentiments = ['anger', 'confusion', 'delight', 'neutral']
            if result['sentiment'] not in valid_sentiments:
                result['sentiment'] = 'neutral'

            # Ensure confidence is a float between 0 and 1
            try:
                result['confidence'] = max(0.0, min(1.0, float(result['confidence'])))
            except (ValueError, TypeError):
                result['confidence'] = 0.5

            # Ensure keywords is a list
            if not isinstance(result['keywords'], list):
                result['keywords'] = []

            # Limit keywords to 5
            result['keywords'] = result['keywords'][:5]

            self.logger.debug(f"Sentiment analysis result: {result}")
            return result

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse Gemini response as JSON: {e}")
            raise Exception(f"Invalid JSON response from Gemini: {e}")
        except Exception as e:
            self.logger.error(f"Error in sentiment analysis: {e}")
            raise

    def get_pending_tickets(self) -> List[Dict]:
        """Retrieve tickets pending sentiment analysis"""
        try:
            tickets_ref = self.db.collection(f'artifacts/{self.app_id}/public/data/raw_tickets')

            # Query for new tickets
            query = tickets_ref.where('status', '==', 'new').limit(self.batch_size)
            docs = query.get()

            tickets = []
            for doc in docs:
                ticket_data = doc.to_dict()
                ticket_data['id'] = doc.id
                tickets.append(ticket_data)

            self.logger.info(f"Retrieved {len(tickets)} pending tickets")
            return tickets

        except Exception as e:
            self.logger.error(f"Error retrieving pending tickets: {e}")
            return []

    def update_ticket_status(self, ticket_id: str, status: str, sentiment_data: Optional[Dict] = None):
        """Update ticket status and sentiment data"""
        try:
            ticket_ref = self.db.collection(f'artifacts/{self.app_id}/public/data/raw_tickets').document(ticket_id)

            update_data = {
                'status': status,
                'processed_timestamp': firestore.SERVER_TIMESTAMP
            }

            if sentiment_data:
                update_data.update({
                    'sentiment': sentiment_data['sentiment'],
                    'summary': sentiment_data['summary'],
                    'confidence': sentiment_data['confidence'],
                    'keywords': sentiment_data['keywords']
                })

            ticket_ref.update(update_data)
            self.logger.debug(f"Updated ticket {ticket_id} with status: {status}")

        except Exception as e:
            self.logger.error(f"Error updating ticket {ticket_id}: {e}")
            raise

    def process_tickets_batch(self):
        """Process a batch of tickets for sentiment analysis"""
        tickets = self.get_pending_tickets()

        if not tickets:
            self.logger.debug("No pending tickets to process")
            return

        processed_count = 0
        error_count = 0

        for ticket in tickets:
            try:
                ticket_id = ticket['id']
                message = ticket.get('message', '')

                if not message.strip():
                    self.logger.warning(f"Ticket {ticket_id} has empty message, marking as error")
                    self.update_ticket_status(ticket_id, 'error')
                    error_count += 1
                    continue

                # Mark as processing
                self.update_ticket_status(ticket_id, 'processing')

                # Analyze sentiment
                sentiment_result = self.analyze_sentiment_with_gemini(message)

                # Update with results
                self.update_ticket_status(ticket_id, 'processed', sentiment_result)
                processed_count += 1

                self.logger.info(f"Processed ticket {ticket_id}: {sentiment_result['sentiment']} "
                               f"(confidence: {sentiment_result['confidence']:.2f})")

                # Rate limiting - wait between API calls
                time.sleep(2)

            except Exception as e:
                self.logger.error(f"Error processing ticket {ticket.get('id', 'unknown')}: {e}")
                try:
                    self.update_ticket_status(ticket['id'], 'error')
                except:
                    pass
                error_count += 1

        self.logger.info(f"Batch processing complete: {processed_count} processed, {error_count} errors")

    def run_continuous(self):
        """Run the processing agent continuously"""
        self.logger.info(f"Starting sentiment processing agent for app: {self.app_id}")
        self.logger.info(f"Processing interval: {self.processing_interval} seconds")
        self.logger.info(f"Batch size: {self.batch_size}")

        def signal_handler(signum, frame):
            self.logger.info("Received shutdown signal")
            self.running = False

        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        while self.running:
            try:
                self.process_tickets_batch()

                # Sleep with interruption check
                for _ in range(self.processing_interval):
                    if not self.running:
                        break
                    time.sleep(1)

            except Exception as e:
                self.logger.error(f"Unexpected error in processing loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying

        self.logger.info("Sentiment processing agent stopped")

if __name__ == "__main__":
    import os
    import sys

    # ALWAYS get APP_ID from environment, not sys.argv!
    app_id = os.environ.get("APP_ID")
    if not app_id:
        print("Set APP_ID in the environment (e.g., .env or Docker Compose)")
        sys.exit(1)

    agent = SentimentProcessingAgent(app_id)
    agent.run_continuous()
