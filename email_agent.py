"""
Email Ingestion Agent for Multi-Agent Sentiment Watchdog System
Monitors email inbox and ingests customer messages into Firebase
"""

import imaplib
import email
import time
import logging
from datetime import datetime
from firebase_admin import firestore
from firebase_admin import credentials
import firebase_admin
from email.header import decode_header
import os
from dotenv import load_dotenv
from retrying import retry
import json

# Load environment variables
load_dotenv()

class EmailIngestionAgent:
    def __init__(self, app_id):
        self.app_id = app_id
        self.setup_logging()
        self.init_firebase()

        # Email configuration
        self.email_server = os.getenv('EMAIL_IMAP_SERVER', 'imap.gmail.com')
        self.email_address = os.getenv('EMAIL_ADDRESS')
        self.email_password = os.getenv('EMAIL_PASSWORD')

        if not self.email_address or not self.email_password:
            raise ValueError("Email credentials not found in environment variables")

    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'email_agent_{self.app_id}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(f'EmailAgent_{self.app_id}')

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

    @retry(stop_max_attempt_number=3, wait_exponential_multiplier=1000)
    def connect_to_email(self):
        """Connect to email server with retry logic"""
        try:
            mail = imaplib.IMAP4_SSL(self.email_server)
            mail.login(self.email_address, self.email_password)
            mail.select('inbox')
            self.logger.info(f"Connected to email server: {self.email_server}")
            return mail
        except Exception as e:
            self.logger.error(f"Failed to connect to email: {e}")
            raise

    def parse_email_header(self, header_value):
        """Parse and decode email headers"""
        if header_value is None:
            return ""

        decoded_header = decode_header(header_value)[0]
        if isinstance(decoded_header[0], bytes):
            encoding = decoded_header[1] or 'utf-8'
            try:
                return decoded_header[0].decode(encoding)
            except (UnicodeDecodeError, LookupError):
                return decoded_header[0].decode('utf-8', errors='ignore')
        return str(decoded_header[0])

    def extract_email_body(self, msg):
        """Extract email body from message"""
        body = ""

        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                cdispo = str(part.get('Content-Disposition'))

                if ctype == 'text/plain' and 'attachment' not in cdispo:
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body = payload.decode('utf-8', errors='ignore')
                            break
                    except Exception as e:
                        self.logger.warning(f"Failed to decode email part: {e}")
        else:
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode('utf-8', errors='ignore')
            except Exception as e:
                self.logger.warning(f"Failed to decode email body: {e}")

        return body.strip()

    def store_email_in_firebase(self, email_data):
        """Store email data in Firestore"""
        try:
            doc_ref = self.db.collection(f'artifacts/{self.app_id}/public/data/raw_tickets').add({
                'source': 'Email',
                'timestamp': firestore.SERVER_TIMESTAMP,
                'message': email_data['body'],
                'subject': email_data['subject'],
                'sender': email_data['sender'],
                'status': 'new',
                'raw_data': {
                    'date': email_data['date'],
                    'message_id': email_data['message_id']
                }
            })

            self.logger.info(f"Stored email from {email_data['sender']} with ID: {doc_ref[1].id}")
            return doc_ref[1].id

        except Exception as e:
            self.logger.error(f"Failed to store email in Firebase: {e}")
            raise

    def fetch_new_emails(self):
        """Fetch and process new emails"""
        mail = None
        try:
            mail = self.connect_to_email()

            # Search for unseen emails
            status, email_ids = mail.search(None, 'UNSEEN')

            if status != 'OK':
                self.logger.warning("Failed to search for emails")
                return

            email_id_list = email_ids[0].split()
            self.logger.info(f"Found {len(email_id_list)} new emails")

            for email_id in email_id_list:
                try:
                    # Fetch email
                    status, msg_data = mail.fetch(email_id, '(RFC822)')

                    if status != 'OK':
                        continue

                    # Parse email
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)

                    # Extract email data
                    email_data = {
                        'sender': self.parse_email_header(msg['From']),
                        'subject': self.parse_email_header(msg['Subject']),
                        'date': self.parse_email_header(msg['Date']),
                        'message_id': self.parse_email_header(msg['Message-ID']),
                        'body': self.extract_email_body(msg)
                    }

                    # Skip emails with empty bodies
                    if not email_data['body'].strip():
                        self.logger.warning(f"Skipping email with empty body from {email_data['sender']}")
                        continue

                    # Store in Firebase
                    self.store_email_in_firebase(email_data)

                except Exception as e:
                    self.logger.error(f"Failed to process email {email_id}: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error in fetch_new_emails: {e}")

        finally:
            if mail:
                try:
                    mail.logout()
                except:
                    pass

    def run_continuous(self, check_interval=300):
        """Run the agent continuously"""
        self.logger.info(f"Starting email ingestion agent for app: {self.app_id}")
        self.logger.info(f"Check interval: {check_interval} seconds")

        while True:
            try:
                self.fetch_new_emails()
                self.logger.info(f"Sleeping for {check_interval} seconds...")
                time.sleep(check_interval)
            except KeyboardInterrupt:
                self.logger.info("Shutting down email agent...")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                time.sleep(60)  # Wait 1 minute before retrying

if __name__ == "__main__":
    import os
    import sys

    app_id = os.environ.get("APP_ID")
    if not app_id:
        print("Set APP_ID in the environment (e.g., via .env or Docker Compose).")
        sys.exit(1)

    agent = EmailIngestionAgent(app_id)
    agent.run_continuous()
