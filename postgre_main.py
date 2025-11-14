import smtplib
import random
import psycopg2
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify
import logging
import os
from flask_cors import CORS

# LOG SETTINGS
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for Unity requests

class DatabaseManager:
    def __init__(self):
        # DATABASE CONFIGURATION FOR POSTGRESQL
        self.db_config = {
            'host': os.getenv('DB_HOST', '176.108.147.162'),
            'user': os.getenv('DB_USER', 'unity_user'),
            'password': os.getenv('DB_PASSWORD', 'donotkys84'),
            'database': os.getenv('DB_NAME', 'unity_db'),
            'port': os.getenv('DB_PORT', '5432'),
        }
    
    def get_connection(self):
        """db_connect for PostgreSQL"""
        try:
            connection = psycopg2.connect(**self.db_config)
            logger.debug("PostgreSQL connection successful")
            return connection
        except psycopg2.Error as e:
            logger.error(f"PostgreSQL connection error: {e}")
            return None
    
    def find_user_by_email(self, email):
        """search_user"""
        connection = self.get_connection()
        if not connection:
            return None
        
        cursor = None
        try:
            cursor = connection.cursor()
            query = "SELECT id, email, reset_password_code, reset_password_code_expiry FROM users WHERE email = %s"
            cursor.execute(query, (email,))
            user_data = cursor.fetchone()
            
            if user_data:
                user = {
                    'id': user_data[0],
                    'email': user_data[1],
                    'reset_password_code': user_data[2],
                    'reset_password_code_expiry': user_data[3]
                }
                logger.debug(f"User found: {email}")
                return user
            else:
                logger.debug(f"User not found: {email}")
                return None
                
        except psycopg2.Error as e:
            logger.error(f"Database error: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            connection.close()
    
    def update_reset_password_data(self, user_id, reset_code, expiry_date):
        """Updating the recovery code and expiration time"""
        connection = self.get_connection()
        if not connection:
            return False
        
        cursor = None
        try:
            cursor = connection.cursor()
            query = """
            UPDATE users 
            SET reset_password_code = %s, reset_password_code_expiry = %s 
            WHERE id = %s
            """
            cursor.execute(query, (reset_code, expiry_date, user_id))
            connection.commit()
            success = cursor.rowcount > 0
            logger.info(f"Updating user data {user_id}: {'successfully' if success else 'failed'}")
            return success
        except psycopg2.Error as e:
            logger.error(f"Error updating recovery data: {e}")
            connection.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            connection.close()

class EmailSender:
    def __init__(self):
        # Email Configuration
        self.config = {
            'email': os.getenv('SMTP_EMAIL', 'minicop.official@gmail.com'),
            'password': os.getenv('SMTP_PASSWORD', 'flrtutqawhamfpac'),
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '465')),
        }
        
    def generate_random_code(self):
        """Generating a random 6-digit code"""
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])
    
    def create_email_message(self, to_email, verification_code):
        """Creating an email message"""
        msg = MIMEMultipart()
        msg['From'] = self.config['email']
        msg['To'] = to_email
        msg['Subject'] = "Password recovery code"
        
        message_body = f"""
        Hello!
 
        Your password recovery code: {verification_code}
        
        Attention! The code is valid for 10 minutes.
 
        If you did not request password recovery, ignore this email.
        
        Sincerely,
        Customer Support.
        """
        
        msg.attach(MIMEText(message_body, 'plain', 'utf-8'))
        return msg
    
    def send_verification_email(self, to_email):
        """Sending verification email"""
        try:
            # Generating the code
            verification_code = self.generate_random_code()
            logger.info(f"Generated code for {to_email}")
            
            # Creating a message
            msg = self.create_email_message(to_email, verification_code)
            
            # Sending via SMTP
            logger.info(f"An attempt to send an email to {to_email}")
            with smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port']) as server:
                server.starttls()
                server.login(self.config['email'], self.config['password'])
                server.send_message(msg)
            
            logger.info(f"Email successfully sent to {to_email}")
            return True, verification_code, f"An email with the verification code has been sent to {to_email}"
        
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error when sending email: {e}")
            return False, None, f"Error sending email: {e}"
        except Exception as e:
            logger.error(f"Unexpected error when sending an email: {e}")
            return False, None, f"Sending error: {str(e)}"

# Creating instances of classes
email_sender = EmailSender()
db_manager = DatabaseManager()

@app.route('/')
def index():
    """The root endpoint for checking the operation of the service"""
    return jsonify({
        'status': 'success',
        'service': 'Password Reset Service',
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
            'send_verification': '/send_verification (POST)',
            'verify_code': '/verify_code (POST)',
            'health': '/health (GET)'
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Checking the database
        db_conn = db_manager.get_connection()
        db_status = 'healthy' if db_conn else 'unhealthy'
        if db_conn:
            db_conn.close()
        
        return jsonify({
            'status': 'success',
            'service': 'healthy',
            'database': db_status,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'service': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/send_verification', methods=['POST'])
def send_verification_email():
    """API endpoint for sending a verification email"""
    try:
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({
                'success': False,
                'message': 'Email is required'
            }), 400
        
        to_email = data['email'].strip().lower()
        logger.info(f"Processing a recovery request for: {to_email}")
        
        # Basic email validation
        if '@' not in to_email or '.' not in to_email:
            return jsonify({
                'success': False,
                'message': 'Invalid email format'
            }), 400
        
        # User search in the database
        user = db_manager.find_user_by_email(to_email)
        if not user:
            logger.warning(f"The user was not found: {to_email}")
            # We return the same response for security reasons.
            return jsonify({
                'success': True,
                'message': 'If the user exists, the code is sent to the email'
            })
        
        logger.info(f"A user has been found: ID {user['id']}")
        
        # Sending email
        success, verification_code, message = email_sender.send_verification_email(to_email)
        
        if success and verification_code:
            # Expiration time calculation
            expiry_date = datetime.now() + timedelta(minutes=10)
            
            # Updating data in the database
            update_success = db_manager.update_reset_password_data(
                user['id'], 
                verification_code, 
                expiry_date
            )
            
            if update_success:
                logger.info(f"The recovery code is saved for the user {user['id']}")
                return jsonify({
                    'success': True,
                    'message': 'If the user exists, the code is sent to the email'
                })
            else:
                logger.error("Couldn't save the code to the database")
                return jsonify({
                    'success': False,
                    'message': 'Error saving data'
                }), 500
        else:
            logger.error(f"Error sending email: {message}")
            return jsonify({
                'success': False,
                'message': 'Error when sending email'
            }), 500
        
    except Exception as e:
        logger.error(f"Request processing error: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

@app.route('/verify_code', methods=['POST'])
def verify_code():
    """endpoint API for verifying the recovery code"""
    try:
        data = request.get_json()
        
        if not data or 'email' not in data or 'code' not in data:
            return jsonify({
                'success': False,
                'message': 'Email and code are required'
            }), 400
        
        email = data['email'].strip().lower()
        code = data['code'].strip()
        
        # User Search
        user = db_manager.find_user_by_email(email)
        if not user:
            return jsonify({
                'success': False,
                'message': 'Invalid code or time expired'
            }), 400
        
        # Checking the code and time
        current_time = datetime.now()
        user_expiry = user.get('reset_password_code_expiry')
        stored_code = user.get('reset_password_code')
        
        if (stored_code and stored_code == code and 
            user_expiry and user_expiry > current_time):
            
            logger.info(f"The code has been confirmed for the user {email}")
            return jsonify({
                'success': True,
                'message': 'The code is correct'
            })
        else:
            logger.warning(f"Invalid or expired code for the user {email}")
            return jsonify({
                'success': False,
                'message': 'Invalid code or time expired'
            }), 400
            
    except Exception as e:
        logger.error(f"Code verification error: {e}")
        return jsonify({
            'success': False,
            'message': 'Code verification error'
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'success': False,
        'message': 'Internal server error'
    }), 500

if __name__ == '__main__':
    logger.info("Starting Password Reset Service with PostgreSQL...")
    # For production, use debug=False
    app.run(host='0.0.0.0', port=5000, debug=False)