"""
Form Ingestion Agent for Multi-Agent Sentiment Watchdog System
Monitors web forms and webhooks for customer feedback
"""

from flask import Flask, request, jsonify
import logging
from datetime import datetime
from firebase_admin import firestore, credentials
import firebase_admin
import os
from dotenv import load_dotenv
import json
import threading
from werkzeug.serving import make_server
import time
import signal
import sys

# Load environment variables
load_dotenv()

class FormIngestionAgent:
    def __init__(self, app_id, port=5000):
        self.app_id = app_id
        self.port = port
        self.setup_logging()
        self.init_firebase()
        self.setup_flask_app()
        self.server = None

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'form_agent_{self.app_id}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(f'FormAgent_{self.app_id}')

    def init_firebase(self):
        try:
            firebase_admin.get_app()
        except ValueError:
            cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH', 'serviceAccountKey.json')
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            else:
                cred_json = os.getenv('FIREBASE_CREDENTIALS_JSON')
                if cred_json:
                    cred_dict = json.loads(cred_json)
                    cred = credentials.Certificate(cred_dict)
                    firebase_admin.initialize_app(cred)
                else:
                    raise ValueError("Firebase credentials not found")
        self.db = firestore.client()
        self.logger.info("Firebase initialized successfully")

    def setup_flask_app(self):
        self.app = Flask(__name__)
        self.app.logger.setLevel(logging.INFO)

        @self.app.route('/health', methods=['GET'])
        def health_check():
            return jsonify({
                'status': 'healthy',
                'agent': 'FormIngestionAgent',
                'app_id': self.app_id,
                'timestamp': datetime.utcnow().isoformat()
            })

        @self.app.route('/webhook/contact-form', methods=['POST'])
        def contact_form_webhook():
            return self.handle_contact_form()

        @self.app.route('/webhook/feedback', methods=['POST'])
        def feedback_webhook():
            return self.handle_feedback_form()

        @self.app.route('/webhook/support', methods=['POST'])
        def support_webhook():
            return self.handle_support_form()

        @self.app.route('/webhook/custom', methods=['POST'])
        def custom_webhook():
            return self.handle_custom_form()

        @self.app.errorhandler(400)
        def bad_request(error):
            self.logger.warning(f"Bad request: {error}")
            return jsonify({'error': 'Bad request', 'message': str(error)}), 400

        @self.app.errorhandler(500)
        def internal_error(error):
            self.logger.error(f"Internal error: {error}")
            return jsonify({'error': 'Internal server error'}), 500

    def validate_form_data(self, data):
        if not isinstance(data, dict):
            return False, "Data must be a JSON object"
        required_fields = ['message']
        for field in required_fields:
            if field not in data or not data[field].strip():
                return False, f"Missing required field: {field}"
        if len(data['message']) > 10000:
            return False, "Message too long (max 10000 characters)"
        return True, "Valid"

    def extract_form_metadata(self, data):
        metadata = {
            'user_agent': request.headers.get('User-Agent', ''),
            'ip_address': request.remote_addr,
            'referer': request.headers.get('Referer', ''),
            'submission_time': datetime.utcnow().isoformat(),
            'form_fields': list(data.keys())
        }
        return metadata

    def store_form_submission(self, form_data, form_type):
        try:
            doc_data = {
                'source': f'Form_{form_type}',
                'timestamp': firestore.SERVER_TIMESTAMP,
                'message': form_data['message'],
                'subject': form_data.get('subject', f'{form_type} Submission'),
                'sender': form_data.get('email', form_data.get('contact_email', 'unknown@unknown.com')),
                'status': 'new',
                'form_type': form_type,
                'raw_data': {
                    'form_fields': {k: v for k, v in form_data.items() if k != 'message'},
                    'metadata': self.extract_form_metadata(form_data)
                }
            }
            if 'name' in form_data:
                doc_data['customer_name'] = form_data['name']
            if 'phone' in form_data:
                doc_data['customer_phone'] = form_data['phone']
            if 'company' in form_data:
                doc_data['customer_company'] = form_data['company']
            doc_ref = self.db.collection(f'artifacts/{self.app_id}/public/data/raw_tickets').add(doc_data)
            self.logger.info(f"Stored {form_type} form submission with ID: {doc_ref[1].id}")
            return doc_ref[1].id
        except Exception as e:
            self.logger.error(f"Failed to store form submission: {e}")
            raise

    def handle_contact_form(self):
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No JSON data provided'}), 400
            is_valid, message = self.validate_form_data(data)
            if not is_valid:
                return jsonify({'error': message}), 400
            submission_id = self.store_form_submission(data, 'Contact')
            return jsonify({
                'status': 'success',
                'message': 'Contact form submitted successfully',
                'submission_id': submission_id
            })
        except Exception as e:
            self.logger.error(f"Error handling contact form: {e}")
            return jsonify({'error': 'Internal server error'}), 500

    def handle_feedback_form(self):
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No JSON data provided'}), 400
            is_valid, message = self.validate_form_data(data)
            if not is_valid:
                return jsonify({'error': message}), 400
            submission_id = self.store_form_submission(data, 'Feedback')
            return jsonify({
                'status': 'success',
                'message': 'Feedback submitted successfully',
                'submission_id': submission_id
            })
        except Exception as e:
            self.logger.error(f"Error handling feedback form: {e}")
            return jsonify({'error': 'Internal server error'}), 500

    def handle_support_form(self):
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No JSON data provided'}), 400
            is_valid, message = self.validate_form_data(data)
            if not is_valid:
                return jsonify({'error': message}), 400
            submission_id = self.store_form_submission(data, 'Support')
            return jsonify({
                'status': 'success',
                'message': 'Support ticket submitted successfully',
                'submission_id': submission_id
            })
        except Exception as e:
            self.logger.error(f"Error handling support form: {e}")
            return jsonify({'error': 'Internal server error'}), 500

    def handle_custom_form(self):
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No JSON data provided'}), 400
            is_valid, message = self.validate_form_data(data)
            if not is_valid:
                return jsonify({'error': message}), 400
            submission_id = self.store_form_submission(data, 'Custom')
            return jsonify({
                'status': 'success',
                'message': 'Form submitted successfully',
                'submission_id': submission_id
            })
        except Exception as e:
            self.logger.error(f"Error handling custom form: {e}")
            return jsonify({'error': 'Internal server error'}), 500

    def start_server(self):
        try:
            self.server = make_server('0.0.0.0', self.port, self.app, threaded=True)
            self.logger.info(f"Form ingestion agent starting on port {self.port}")
            self.logger.info("Webhook endpoints available:")
            self.logger.info(f"  - Health check: http://localhost:{self.port}/health")
            self.logger.info(f"  - Contact form: http://localhost:{self.port}/webhook/contact-form")
            self.logger.info(f"  - Feedback form: http://localhost:{self.port}/webhook/feedback")
            self.logger.info(f"  - Support form: http://localhost:{self.port}/webhook/support")
            self.logger.info(f"  - Custom form: http://localhost:{self.port}/webhook/custom")
            self.server.serve_forever()
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            raise

    def stop_server(self):
        if self.server:
            self.logger.info("Stopping form ingestion agent...")
            self.server.shutdown()

    def run(self):
        def signal_handler(signum, frame):
            self.logger.info("Received shutdown signal")
            self.stop_server()
            sys.exit(0)
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        self.start_server()

if __name__ == "__main__":
    import os
    import sys
    app_id = os.environ.get("APP_ID")
    if not app_id:
        print("Set APP_ID in environment (e.g., via .env or Docker Compose).")
        sys.exit(1)
    port = int(os.environ.get("PORT", "5000"))
    agent = FormIngestionAgent(app_id, port)
    agent.run()
