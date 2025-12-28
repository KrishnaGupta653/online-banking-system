import os
import logging
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import psycopg2
from psycopg2 import pool
import psycopg2.extras
import random
from flask_mail import Mail, Message
import requests
from cryptography.fernet import Fernet
import qrcode
from io import BytesIO
import base64
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from dotenv import load_dotenv
from functools import wraps
import hashlib
import secrets
from decimal import Decimal
from datetime import datetime, timezone, timedelta
import urllib.parse as urlparse
import resend
# Add these imports with your other imports
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

load_dotenv()
resend.api_key = os.getenv('RESEND_API_KEY')

app = Flask(__name__, static_folder='static')

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

if not app.debug:
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

# Security configurations
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))

# Rate limiting with Redis (for production)
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=os.getenv('REDIS_URL', 'memory://')
)

# Content Security Policy
csp = {
    'default-src': "'self'",
    'script-src': [
        "'self'",
        "'unsafe-inline'",  # Only for reCAPTCHA - remove if possible
        "https://www.google.com",
        "https://www.gstatic.com",
        "https://cdnjs.cloudflare.com",
        "https://unpkg.com"
    ],
    'style-src': ["'self'", "'unsafe-inline'"],
    'img-src': ["'self'", "data:", "https:"],
    'connect-src': ["'self'", "https://www.google.com"],
    'frame-src': ["https://www.google.com"]
}

# Force HTTPS in production, set security headers
if os.getenv('FLASK_ENV') == 'production':
    Talisman(app, 
             force_https=True,
             strict_transport_security=True,
             content_security_policy=csp,
             referrer_policy='strict-origin-when-cross-origin')

# Database Configuration
def get_MYSQL_connection():
    """Get PostgreSQL database connection"""
    try:
        # Parse DATABASE_URL if provided (for Render/Heroku)
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            # Parse the URL
            url = urlparse.urlparse(database_url)
            conn = psycopg2.connect(
                host=url.hostname,
                database=url.path[1:],
                user=url.username,
                password=url.password,
                port=url.port or 5432,
                sslmode='disable'  # Required for Render
            )
        else:
            # Use individual environment variables
            conn = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                database=os.getenv('POSTGRES_DB', 'bank'),
                user=os.getenv('POSTGRES_USER'),
                password=os.getenv('POSTGRES_PASSWORD'),
                port=os.getenv('POSTGRES_PORT', 5432),
                sslmode='require' if os.getenv('FLASK_ENV') == 'production' else 'prefer'
            )
        return conn
    except Exception as e:
        app.logger.error(f"Database connection failed: {str(e)}")
        raise

# Database helper functions
def execute_query(query, params=None, fetch=None):
    """Execute database query with proper error handling"""
    conn = None
    cursor = None
    try:
        conn = get_MYSQL_connection()
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        
        if fetch == 'one':
            result = cursor.fetchone()
        elif fetch == 'all':
            result = cursor.fetchall()
        else:
            result = None
            
        conn.commit()
        return result
    except Exception as e:
        if conn:
            conn.rollback()
        app.logger.error(f"Database query failed: {str(e)}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Encryption setup
key = os.getenv('ENCRYPTION_KEY').encode()
cipher_suite = Fernet(key)

RECAPTCHA_SITE_KEY = os.getenv('RECAPTCHA_SITE_KEY')
RECAPTCHA_SECRET_KEY = os.getenv('RECAPTCHA_SECRET_KEY')

def encrypt_password(password):
    password_bytes = password.encode('utf-8')
    encrypted_bytes = cipher_suite.encrypt(password_bytes)
    # Always return as Base64 string
    return base64.b64encode(encrypted_bytes).decode('utf-8')

def decrypt_password(encrypted_password):
    try:
        if isinstance(encrypted_password, memoryview):
            encrypted_bytes = bytes(encrypted_password)
        elif isinstance(encrypted_password, str):
            if encrypted_password.startswith('\\x'):
                # Handle PostgreSQL hex format
                hex_string = encrypted_password[2:]
                encrypted_bytes = bytes.fromhex(hex_string)
            else:
                # Handle Base64 format
                encrypted_bytes = base64.b64decode(encrypted_password.encode('utf-8'))
        else:
            encrypted_bytes = encrypted_password
            
        decrypted_password_bytes = cipher_suite.decrypt(encrypted_bytes)
        return decrypted_password_bytes.decode('utf-8')
    except Exception as e:
        app.logger.error(f"Decryption error: {str(e)}")
        raise

def is_account_number_unique(account_number):
    query = "SELECT COUNT(*) FROM accounts WHERE account_number = %s"
    result = execute_query(query, (account_number,), fetch='one')
    return result[0] == 0

def generate_unique_account_number():
    while True:
        account_number = ''.join(random.choice('0123456789') for _ in range(10))
        if is_account_number_unique(account_number):
            return account_number

def is_user_id_unique(user_id):
    query = "SELECT COUNT(*) FROM accounts WHERE user_id = %s"
    result = execute_query(query, (user_id,), fetch='one')
    return result[0] == 0

def generate_unique_user_id():
    while True:
        user_id = ''.join(random.choice('0123456789') for _ in range(5))
        if is_user_id_unique(user_id):
            return user_id

def verify_recaptcha(recaptcha_response):
    """Verify reCAPTCHA response with Google"""
    if not recaptcha_response:
        return False
    data = {
        'secret': RECAPTCHA_SECRET_KEY,
        'response': recaptcha_response
    }
    try:
        response = requests.post('https://www.google.com/recaptcha/api/siteverify', 
                               data=data, timeout=10)
        result = response.json()
        app.logger.info(f"reCAPTCHA verification result: {result}")
        # For reCAPTCHA v3, check score as well
        if result.get('success') and result.get('score', 0) > 0.5:
            return True
    except Exception as e:
        app.logger.error(f"reCAPTCHA verification error: {e}")
    return False

# Mail configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'false').lower() == 'true'

mail = Mail(app)

# Security decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
# @app.route('/send_otp', methods=['POST'])
# @limiter.limit("5 per minute")
# def send_otp():
#     if request.method == 'POST':
#         email = request.form.get('email_id')
#         if not email:
#             return jsonify({'success': False, 'error_message': 'Email is required'})
            
#         # Generate a random OTP
#         correct_otp = str(random.randint(1000, 9999))
#         session['correct_otp'] = correct_otp
#         session['otp_timestamp'] = datetime.now()
        
#         msg = Message('Your Banking OTP', 
#                      sender=os.getenv('MAIL_USERNAME'), 
#                      recipients=[email])
#         msg.body = f'Your OTP for bank account creation is: {correct_otp}\n\nThis OTP will expire in 10 minutes.'
        
#         try:
#             mail.send(msg)
#             app.logger.info(f"OTP sent to {email}")
#             return jsonify({'success': True})
#         except Exception as e:
#             app.logger.error(f"Failed to send OTP: {str(e)}")
#             return jsonify({'success': False, 'error_message': 'Failed to send OTP'})


# @app.route('/send_otp', methods=['POST'])
# @limiter.limit("5 per minute")
# def send_otp():
#     """Send OTP via Resend API"""
#     try:
#         email = request.form.get('email_id')
        
#         # Validation
#         if not email:
#             app.logger.error("No email provided")
#             return jsonify({
#                 'success': False, 
#                 'error_message': 'Email is required'
#             })
        
#         # Generate OTP
#         correct_otp = str(random.randint(1000, 9999))
#         session['correct_otp'] = correct_otp
#         session['otp_timestamp'] = datetime.now(timezone.utc)
        
#         app.logger.info(f"Generated OTP {correct_otp} for {email}")
        
#         # Create professional HTML email
#         html_body = f"""
#         <!DOCTYPE html>
#         <html>
#         <head>
#             <style>
#                 body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 0; }}
#                 .container {{ max-width: 600px; margin: 0 auto; }}
#                 .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px 20px; text-align: center; }}
#                 .header h1 {{ margin: 0; font-size: 28px; }}
#                 .content {{ padding: 40px 30px; background-color: #f8f9fa; }}
#                 .otp-box {{ 
#                     background-color: white; 
#                     padding: 30px; 
#                     text-align: center; 
#                     margin: 25px 0;
#                     border-radius: 10px;
#                     box-shadow: 0 4px 6px rgba(0,0,0,0.1);
#                 }}
#                 .otp-code {{ 
#                     color: #667eea; 
#                     font-size: 56px; 
#                     font-weight: bold;
#                     letter-spacing: 18px; 
#                     margin: 10px 0;
#                     font-family: 'Courier New', monospace;
#                 }}
#                 .warning {{ 
#                     background-color: #fff3cd; 
#                     border-left: 4px solid #ffc107; 
#                     padding: 15px; 
#                     margin: 20px 0;
#                     border-radius: 4px;
#                 }}
#                 .footer {{ 
#                     color: #6c757d; 
#                     font-size: 13px; 
#                     margin-top: 30px; 
#                     padding-top: 20px;
#                     border-top: 2px solid #dee2e6;
#                     text-align: center;
#                 }}
#             </style>
#         </head>
#         <body>
#             <div class="container">
#                 <div class="header">
#                     <h1>🏦 Banking System</h1>
#                     <p style="margin: 10px 0 0 0; font-size: 16px;">Secure Account Verification</p>
#                 </div>
#                 <div class="content">
#                     <h2 style="color: #333; margin-top: 0;">Your One-Time Password</h2>
#                     <p style="color: #555; font-size: 16px;">You requested an OTP to create a new bank account. Please use the code below to complete your registration:</p>
                    
#                     <div class="otp-box">
#                         <p style="margin: 0; color: #6c757d; font-size: 14px; text-transform: uppercase; letter-spacing: 2px;">Your OTP Code</p>
#                         <p class="otp-code">{correct_otp}</p>
#                         <p style="margin: 0; color: #6c757d; font-size: 14px;">Valid for 10 minutes</p>
#                     </div>
                    
#                     <div class="warning">
#                         <strong>⏰ Important:</strong> This OTP will expire in 10 minutes for your security.
#                     </div>
                    
#                     <div class="footer">
#                         <p><strong>🔒 Security Tips:</strong></p>
#                         <p>• Never share this OTP with anyone, including bank employees<br>
#                         • We will never ask for your OTP via phone or email<br>
#                         • If you didn't request this, please ignore this email</p>
#                         <p style="margin-top: 20px; color: #adb5bd;">© 2024 Banking System. All rights reserved.</p>
#                     </div>
#                 </div>
#             </div>
#         </body>
#         </html>
#         """
        
#         # Plain text fallback
#         text_body = f"""
# Banking System - Your OTP Code

# Your OTP for bank account creation is: {correct_otp}

# This OTP will expire in 10 minutes.

# Security reminder: Never share this OTP with anyone.

# If you didn't request this, please ignore this email.
#         """
        
#         # Send email via Resend
#         try:
#             params = {
#                 "from": "Banking System <onboarding@resend.dev>",
#                 "to": [email],
#                 "subject": "Your Banking OTP - Valid for 10 Minutes",
#                 "html": html_body,
#                 "text": text_body
#             }
            
#             result = resend.Emails.send(params)
            
#             app.logger.info(f"✅ OTP sent successfully via Resend. Email ID: {result.get('id')}")
#             return jsonify({
#                 'success': True,
#                 'message': 'OTP sent successfully to your email'
#             })
            
#         except Exception as email_error:
#             app.logger.error(f"❌ Resend API error: {str(email_error)}", exc_info=True)
#             return jsonify({
#                 'success': False, 
#                 'error_message': 'Failed to send OTP. Please check your email address and try again.'
#             })
            
#     except Exception as e:
#         app.logger.error(f"❌ OTP generation error: {str(e)}", exc_info=True)
#         return jsonify({
#             'success': False, 
#             'error_message': 'An error occurred. Please try again.'
#         })


@app.route('/send_otp', methods=['POST'])
@limiter.limit("5 per minute")
def send_otp():
    """
    Send OTP via Brevo Transactional Email API
    FREE: 300 emails/day forever
    """
    try:
        # Get email from form
        email = request.form.get('email_id')
        
        # Validation
        if not email or not email.strip():
            app.logger.error("No email provided")
            return jsonify({
                'success': False, 
                'error_message': 'Email address is required'
            })
        
        # Generate 4-digit OTP
        correct_otp = str(random.randint(1000, 9999))
        
        # Store in session with timestamp
        session['correct_otp'] = correct_otp
        session['otp_timestamp'] = datetime.now(timezone.utc)
        
        app.logger.info(f"🔐 Generated OTP {correct_otp} for {email}")
        
        # ==========================================
        # CREATE HTML EMAIL CONTENT
        # ==========================================
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            background-color: #f5f5f5;
            padding: 20px;
        }}
        .email-container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 10px;
        }}
        .header p {{
            font-size: 16px;
            opacity: 0.95;
        }}
        .content {{
            padding: 40px 30px;
        }}
        .greeting {{
            font-size: 18px;
            color: #333;
            margin-bottom: 20px;
        }}
        .message {{
            font-size: 16px;
            color: #555;
            line-height: 1.8;
            margin-bottom: 30px;
        }}
        .otp-box {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 10px;
            padding: 30px;
            text-align: center;
            margin: 30px 0;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.06);
        }}
        .otp-label {{
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: #666;
            font-weight: 600;
            margin-bottom: 15px;
        }}
        .otp-code {{
            font-size: 48px;
            font-weight: bold;
            color: #667eea;
            letter-spacing: 15px;
            font-family: 'Courier New', monospace;
            margin: 10px 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }}
        .otp-expiry {{
            font-size: 14px;
            color: #666;
            margin-top: 15px;
        }}
        .warning-box {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px 20px;
            margin: 25px 0;
            border-radius: 4px;
        }}
        .warning-box p {{
            color: #856404;
            font-size: 14px;
            margin: 5px 0;
        }}
        .security-section {{
            background-color: #f8f9fa;
            padding: 25px;
            border-radius: 8px;
            margin: 25px 0;
            border: 1px solid #dee2e6;
        }}
        .security-section h3 {{
            color: #333;
            font-size: 18px;
            margin-bottom: 15px;
        }}
        .security-section ul {{
            list-style: none;
            padding: 0;
        }}
        .security-section li {{
            color: #555;
            font-size: 14px;
            padding: 8px 0;
            padding-left: 25px;
            position: relative;
        }}
        .security-section li:before {{
            content: "✓";
            position: absolute;
            left: 0;
            color: #28a745;
            font-weight: bold;
        }}
        .footer {{
            text-align: center;
            padding: 30px;
            background-color: #f8f9fa;
            color: #6c757d;
            font-size: 13px;
            border-top: 1px solid #dee2e6;
        }}
        .footer p {{
            margin: 5px 0;
        }}
        @media only screen and (max-width: 600px) {{
            .header {{ padding: 30px 20px; }}
            .content {{ padding: 30px 20px; }}
            .otp-code {{ font-size: 36px; letter-spacing: 10px; }}
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <!-- Header -->
        <div class="header">
            <h1>🏦 Banking System</h1>
            <p>Secure Account Verification</p>
        </div>
        
        <!-- Main Content -->
        <div class="content">
            <div class="greeting">
                Hello,
            </div>
            
            <div class="message">
                You requested a One-Time Password (OTP) to create a new bank account. 
                Please use the verification code below to complete your registration:
            </div>
            
            <!-- OTP Box -->
            <div class="otp-box">
                <div class="otp-label">Your OTP Code</div>
                <div class="otp-code">{correct_otp}</div>
                <div class="otp-expiry">⏱️ Valid for 10 minutes only</div>
            </div>
            
            <!-- Warning -->
            <div class="warning-box">
                <p><strong>⚠️ Important:</strong> This OTP will expire in 10 minutes for your security.</p>
            </div>
            
            <!-- Security Tips -->
            <div class="security-section">
                <h3>🔒 Security Guidelines</h3>
                <ul>
                    <li>Never share this OTP with anyone, including bank employees</li>
                    <li>Our team will never ask for your OTP via phone or email</li>
                    <li>If you didn't request this code, please ignore this email</li>
                    <li>Always verify you're on our official website before entering OTP</li>
                </ul>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <p><strong>Banking System</strong></p>
            <p>Secure • Reliable • Trusted</p>
            <p style="margin-top: 15px;">© 2024 Banking System. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """
        
        # Plain text version (for email clients that don't support HTML)
        text_content = f"""
Banking System - Your OTP Code

Hello,

Your One-Time Password (OTP) for bank account creation is:

    {correct_otp}

This OTP is valid for 10 MINUTES ONLY.

SECURITY REMINDERS:
✓ Never share this OTP with anyone
✓ We will never ask for your OTP via phone or email
✓ If you didn't request this, please ignore this email

© 2024 Banking System
Secure • Reliable • Trusted
        """
        
        # ==========================================
        # SEND EMAIL VIA BREVO API
        # ==========================================
        try:
            # Configure Brevo API
            configuration = sib_api_v3_sdk.Configuration()
            configuration.api_key['api-key'] = os.getenv('BREVO_API_KEY')
            
            # Create API instance for transactional emails
            api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
                sib_api_v3_sdk.ApiClient(configuration)
            )
            
            # Define sender
            sender = {
                "name": os.getenv('BREVO_SENDER_NAME', 'Banking System'),
                "email": os.getenv('BREVO_SENDER_EMAIL', 'krishna3657777@gmail.com')
            }
            
            # Define recipient
            to = [{"email": email}]
            
            # Create email object
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=to,
                sender=sender,
                subject="🏦 Your Banking OTP - Valid for 10 Minutes",
                html_content=html_content,
                text_content=text_content
            )
            
            # Send the email
            api_response = api_instance.send_transac_email(send_smtp_email)
            
            # Success
            app.logger.info(f"✅ OTP sent successfully via Brevo to {email}")
            app.logger.info(f"📧 Brevo Message ID: {api_response.message_id}")
            
            return jsonify({
                'success': True,
                'message': 'OTP sent successfully! Please check your email.'
            })
            
        except ApiException as e:
            # Brevo API error
            error_body = e.body if hasattr(e, 'body') else str(e)
            app.logger.error(f"❌ Brevo API error: {error_body}", exc_info=True)
            
            return jsonify({
                'success': False, 
                'error_message': 'Failed to send OTP. Please check your email address and try again.'
            })
            
    except Exception as e:
        # General error
        app.logger.error(f"❌ Unexpected error in send_otp: {str(e)}", exc_info=True)
        return jsonify({
            'success': False, 
            'error_message': 'An unexpected error occurred. Please try again.'
        })

@app.route('/')
def index():
    return render_template('index.html', recaptcha_site_key=RECAPTCHA_SITE_KEY)

@app.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    if request.method == 'POST':
        # Verify reCAPTCHA
        recaptcha_response = request.form.get('g-recaptcha-response')
        if not verify_recaptcha(recaptcha_response):
            flash('reCAPTCHA verification failed. Please try again.', 'error')
            return redirect(url_for('index'))
        
        user_id = request.form['user_id']
        password = request.form['password']
        
        # Input validation
        if not user_id or not password:
            flash('Please enter both User ID and password.', 'error')
            return redirect(url_for('index'))
        
        try:
            # Use parameterized query to prevent SQL injection
            query = "SELECT encrypted_password FROM accounts WHERE user_id = %s"
            encrypted_passwords = execute_query(query, (user_id,), fetch='all')
            
            for encrypted_password in encrypted_passwords:
                stored_password = decrypt_password(encrypted_password[0])
                if password == stored_password:
                    session['user_id'] = user_id
                    session.permanent = True
                    app.logger.info(f"User {user_id} logged in successfully")
                    return redirect(url_for('account', user_id=user_id))
            
            app.logger.warning(f"Failed login attempt for user_id: {user_id}")
            flash('Login failed. Please check your username and password.', 'error')
            
        except Exception as e:
            app.logger.error(f"Login error: {str(e)}")
            flash('An error occurred during login. Please try again.', 'error')
    
    return redirect(url_for('index'))

@app.route('/account/<user_id>')
@login_required
def account(user_id):
    # Security check: ensure user can only access their own account
    if session.get('user_id') != user_id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('index'))
    
    try:
        # Fetch user details - Fixed query to match backup structure
        user_query = """
            SELECT user_id, date_of_birth, Verification_id_no, account_holder_name, contact_no 
            FROM accounts WHERE user_id = %s LIMIT 1
        """
        user_details = execute_query(user_query, (user_id,), fetch='one')
        
        if not user_details:
            flash('User not found.', 'error')
            return redirect(url_for('index'))
        
        # Extract user details
        user_id_val = user_details[0]
        date_of_birth = user_details[1]
        verification_id_no = user_details[2]  # Fixed column name
        account_holder_name = user_details[3]
        contact_no = user_details[4]
        
        # Fetch all accounts for this user
        accounts_query = "SELECT * FROM accounts WHERE user_id = %s"
        accounts_data = execute_query(accounts_query, (user_id,), fetch='all')
        
        bank_accounts = []
        total_balance = 0
        
        for account_data in accounts_data:
            bank_account_details = {
                'bank_name': account_data[2],
                'account_id': account_data[0],
                'account_number': account_data[3],
                'account_type_name': account_data[4],
                'password': account_data[11],
                'account_opening_date': account_data[13],
                'balance': account_data[14]
            }
            bank_accounts.append(bank_account_details)
            total_balance += account_data[14]
        
        session['bank_accounts'] = bank_accounts
        
        # Fetch transaction history
        transaction_query = "SELECT * FROM transaction_history WHERE user_id = %s ORDER BY transaction_date DESC"
        transaction_data = execute_query(transaction_query, (user_id,), fetch='all')
        
        # Get additional user info from the first account record
        first_account = accounts_data[0] if accounts_data else None
        email_id = first_account[9] if first_account else ""
        address = first_account[10] if first_account else ""
        
        return render_template('Account.html', 
                             user_id=user_id_val,
                             date_of_birth=date_of_birth,
                             Verification_id_no=verification_id_no,  # Fixed variable name
                             account_holder_name=account_holder_name,
                             contact_no=contact_no,
                             email_id=email_id,  # Added missing field
                             address=address,    # Added missing field
                             bank_accounts=bank_accounts,
                             account_data=first_account,  # Pass first account data
                             total_balance=total_balance,
                             transaction_data=transaction_data)
                             
    except Exception as e:
        app.logger.error(f"Error loading account page: {str(e)}")
        flash('An error occurred loading your account.', 'error')
        return redirect(url_for('index'))
@app.route('/new_account')
def new_account():
    return render_template('New_account.html', form=request.form)

@app.route('/create_account', methods=['POST'])
@limiter.limit("3 per minute")
def create_account():
    if request.method == 'POST':
        try:
            # Validate OTP first
            entered_otp = request.form.get('otp')
            correct_otp = session.get('correct_otp')
            otp_timestamp = session.get('otp_timestamp')
            
            if not entered_otp or not correct_otp:
                flash('Please request and enter OTP.', 'error')
                return render_template('New_account.html', form=request.form)
            
            # Check OTP expiry (10 minutes)
            # if otp_timestamp and datetime.now(timezone.utc).replace(tzinfo=None) - otp_timestamp.replace(tzinfo=None) > timedelta(minutes=10):
            #     session.pop('correct_otp', None)
            #     session.pop('otp_timestamp', None)
            #     flash('OTP has expired. Please request a new one.', 'error')
            #     return render_template('New_account.html', form=request.form)
            # Check OTP expiry (10 minutes)
            if otp_timestamp:
                time_elapsed = datetime.now(timezone.utc) - otp_timestamp
                if time_elapsed > timedelta(minutes=10):
                    session.pop('correct_otp', None)
                    session.pop('otp_timestamp', None)
                    flash('OTP has expired. Please request a new one.', 'error')
                    return render_template('New_account.html', form=request.form)
            
            if entered_otp != correct_otp:
                flash('Invalid OTP. Please try again.', 'error')
                return render_template('New_account.html', form=request.form)
            
            # Get form data
            account_type_name = request.form.get('account_type_name')
            date_of_birth = request.form.get('date_of_birth')
            bank = request.form.get('bank')
            verification_id_no = request.form.get('Verification_id_no')
            account_holder_name = request.form.get('account_holder_name')
            contact_no = request.form.get('contact_no')
            email_id = request.form.get('email_id')
            address = request.form.get('address')
            password = request.form.get('password')
            account_opening_date = request.form.get('account_opening_date')
            balance = request.form.get('balance')
            
            # Validate required fields
            required_fields = [account_type_name, date_of_birth, bank, verification_id_no, 
                             account_holder_name, contact_no, email_id, address, 
                             password, account_opening_date, balance]
            
            if not all(required_fields):
                flash('All fields are required.', 'error')
                return render_template('New_account.html', form=request.form)
            
            # Check if user already exists by verification ID
            check_verification_query = "SELECT user_id FROM accounts WHERE verification_id_no = %s"
            existing_user = execute_query(check_verification_query, (verification_id_no,), fetch='one')
            
            if existing_user:
                user_id = existing_user[0]
            else:
                user_id = generate_unique_user_id()
            
            account_number = generate_unique_account_number()
            encrypted_password = encrypt_password(password)
            
            # Insert new account
            insert_query = """
                INSERT INTO accounts (
                    user_id, account_number, bank, account_type_name, date_of_birth,
                    verification_id_no, account_holder_name, contact_no, email_id,
                    address, password, encrypted_password, account_opening_date, balance
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (user_id, account_number, bank, account_type_name, date_of_birth,
                     verification_id_no, account_holder_name, contact_no, email_id,
                     address, password, encrypted_password, account_opening_date, balance)
            
            execute_query(insert_query, values)
            
            # Clear OTP from session
            session.pop('correct_otp', None)
            session.pop('otp_timestamp', None)
            
            app.logger.info(f"New account created for user_id: {user_id}")
            return redirect('/account_created_successfully')
            
        except Exception as e:
            app.logger.error(f"Account creation error: {str(e)}")
            flash('An error occurred creating your account. Please try again.', 'error')
            return render_template('New_account.html', form=request.form)

@app.route('/account_created_successfully')
def account_created_successfully():
    try:
        # Get the most recently created account
        query = "SELECT * FROM accounts ORDER BY account_id DESC LIMIT 1"
        account_data = execute_query(query, fetch='one')
        
        if account_data:
            return render_template('Account_created_successfully.html', account_data=account_data)
        else:
            flash('Account not found.', 'error')
            return redirect(url_for('index'))
            
    except Exception as e:
        app.logger.error(f"Error loading account creation success page: {str(e)}")
        flash('An error occurred.', 'error')
        return redirect(url_for('index'))

@app.route('/home')
def home():
    return render_template('Home.html')

@app.route('/contacts')
def contacts():
    return render_template('Contact_Us.html')

@app.route('/qr_code')
@login_required
def qr_code():
    try:
        user_id = session.get('user_id')
        accounts_query = "SELECT * FROM accounts WHERE user_id = %s"
        user_accounts = execute_query(accounts_query, (user_id,), fetch='all')
        
        qr_code_images = []
        for account in user_accounts:
            account_number = account[3]
            bank = account[2]
            account_holder_name = account[7]
            contact_no = account[8]
            
            # Generate the QR code image
            qr_code_data = f"Account Holder: {account_holder_name}\nAccount Number: {account_number}\nContact Number: {contact_no}"
            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
            qr.add_data(qr_code_data)
            qr.make(fit=True)
            qr_code_image = qr.make_image(fill_color="black", back_color="white")
            qr_code_buffer = BytesIO()
            qr_code_image.save(qr_code_buffer, format='PNG')
            qr_code_image_data = base64.b64encode(qr_code_buffer.getvalue()).decode('utf-8')
            qr_code_images.append({'image': qr_code_image_data, 'account_number': account_number, 'bank': bank})
        
        return render_template('QR_code.html', qr_code_images=qr_code_images)
        
    except Exception as e:
        app.logger.error(f"Error generating QR codes: {str(e)}")
        flash('An error occurred generating QR codes.', 'error')
        return redirect(url_for('account', user_id=session.get('user_id')))

@app.route('/payment_and_transfer', methods=['GET', 'POST'])
@login_required
def payment_and_transfer():
    bank_accounts = session.get('bank_accounts', [])
    return render_template('Payment.html', user_accounts=bank_accounts)

@app.route('/make_payment', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def make_payment():
    try:
        user_id = session.get('user_id')
        recipient_name = request.form.get('recipient_name')
        recipient_type = request.form.get('recipient_type')
        recipient_no = request.form.get('recipient_account_number' if recipient_type == 'account' else 'recipient_phone_number')
        transaction_description = request.form.get('transaction_description')
        transaction_date = request.form.get('transaction_date')
        transaction_amount = Decimal(request.form.get('amount', 0))
        selected_account_id = int(request.form.get('selected_account_id'))
        
        # Validate inputs
        if transaction_amount <= 0:
            flash('Transaction amount must be positive.', 'error')
            return redirect(url_for('payment_and_transfer'))
        
        # Get account details and current balance
        balance_query = "SELECT balance, bank FROM accounts WHERE account_id = %s AND user_id = %s"
        account_info = execute_query(balance_query, (selected_account_id, user_id), fetch='one')
        
        if not account_info:
            flash('Invalid account selected.', 'error')
            return redirect(url_for('payment_and_transfer'))
        
        current_balance, bank = account_info
        
        if transaction_amount > current_balance:
            flash('Insufficient balance!', 'error')
            return redirect(url_for('payment_and_transfer'))
        
        # Update balance
        new_balance = current_balance - transaction_amount
        update_query = "UPDATE accounts SET balance = %s WHERE account_id = %s"
        execute_query(update_query, (new_balance, selected_account_id))
        
        # Insert transaction record
        insert_query = """
            INSERT INTO transaction_history (
                account_id, user_id, bank, transaction_date, recipient_name,
                transaction_description, recipient_type, recipient_no, transaction_amount
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (selected_account_id, user_id, bank, transaction_date, recipient_name,
                 transaction_description, recipient_type, recipient_no, transaction_amount)
        execute_query(insert_query, values)
        
        app.logger.info(f"Payment successful: User {user_id}, Amount: {transaction_amount}")
        flash('Payment successful!', 'success')
        return redirect(url_for('account', user_id=user_id))
        
    except Exception as e:
        app.logger.error(f"Payment error: {str(e)}")
        flash('An error occurred while processing the payment.', 'error')
        return redirect(url_for('payment_and_transfer'))

@app.route('/apply_loan', methods=['GET', 'POST'])
def apply_loan():
    if request.method == 'POST':
        try:
            # Get form data
            form_data = {
                'applicant_name': request.form.get('applicant_name'),
                'date_of_birth': request.form.get('date_of_birth'),
                'verification_id_no': request.form.get('Verification_id_no'),
                'contact_no': request.form.get('contact_no'),
                'email_id': request.form.get('email_id'),
                'address': request.form.get('address'),
                'job_title': request.form.get('job_title'),
                'loan_type': request.form.get('loan_type'),
                'loan_amount': request.form.get('loan_amount'),
                'loan_term': request.form.get('loan_term'),
                'credit_score': request.form.get('credit_score'),
                'application_date': request.form.get('application_date')
            }
            
            # Validate required fields
            if not all(form_data.values()):
                flash('All fields are required.', 'error')
                return render_template('Loan_Apply.html')
            
            insert_query = """
                INSERT INTO loan (
                    applicant_name, date_of_birth, verification_id_no, contact_no,
                    email_id, address, job_title, loan_type, loan_amount,
                    loan_term, credit_score, application_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = tuple(form_data.values())
            execute_query(insert_query, values)
            
            app.logger.info(f"Loan application submitted: {form_data['applicant_name']}")
            return redirect(url_for('loan_app_suc'))
            
        except Exception as e:
            app.logger.error(f"Loan application error: {str(e)}")
            flash('An error occurred submitting your loan application.', 'error')
    
    return render_template('Loan_Apply.html')

@app.route('/loan_app_suc')
def loan_app_suc():
    try:
        query = "SELECT * FROM loan ORDER BY loan_id DESC LIMIT 1"
        account_data = execute_query(query, fetch='one')
        
        if account_data:
            return render_template('Loan_app_suc.html', account_data=account_data)
        else:
            flash('Loan application not found.', 'error')
            return redirect(url_for('apply_loan'))
            
    except Exception as e:
        app.logger.error(f"Error loading loan success page: {str(e)}")
        flash('An error occurred.', 'error')
        return redirect(url_for('apply_loan'))

@app.route('/view_loan_status', methods=["GET", "POST"])
def view_loan_status():
    loan_data = None
    
    if request.method == "POST":
        try:
            loan_id = request.form.get("loan_id")
            
            # Validate loan_id input
            if not loan_id or not loan_id.strip():
                flash('Please enter a valid loan ID.', 'error')
                return render_template("View_loan_status.html", loan=None)
            
            # Convert to integer to validate it's a number
            try:
                loan_id = int(loan_id.strip())
            except ValueError:
                flash('Loan ID must be a number.', 'error')
                return render_template("View_loan_status.html", loan=None)
            
            # Query the database to get the loan status
            query = "SELECT * FROM loan WHERE loan_id = %s"
            loan_record = execute_query(query, (loan_id,), fetch='one')
            
            if loan_record:
                loan_data = {
                    'loan_id': loan_record[0],
                    'applicant_name': loan_record[1],
                    'date_of_birth': loan_record[2],
                    'verification_id_no': loan_record[3],
                    'contact_no': loan_record[4],
                    'email_id': loan_record[5],
                    'address': loan_record[6],
                    'job_title': loan_record[7],
                    'loan_type': loan_record[8],
                    'loan_amount': loan_record[9],
                    'loan_term': loan_record[10],
                    'credit_score': loan_record[11],
                    'application_date': loan_record[12],  # Note: this is application_date, not applicant_date
                    'status': loan_record[13]
                }
                
                app.logger.info(f"Loan status retrieved for loan_id: {loan_id}")
                return render_template("View_loan_status.html", loan=loan_data)
            else:
                flash("Loan ID not found. Please check the loan ID and try again.", 'error')
                app.logger.warning(f"Loan ID not found: {loan_id}")
                
        except Exception as e:
            app.logger.error(f"View loan status error: {str(e)}")
            flash("An error occurred while retrieving loan status. Please try again.", 'error')
    
    return render_template("View_loan_status.html", loan=loan_data)

@app.route('/forgot')
def forgot():
    return render_template('Forgot.html')

@app.route('/forgotten', methods=['POST', 'GET'])
@limiter.limit("5 per minute")
def forgotten():
    user_id_result = ""
    password_result = ""
    
    if request.method == 'POST':
        try:
            recipient_type = request.form.get('option')
            
            if recipient_type == 'user_id':
                account_id = request.form.get('account_id_user')
                verification_id = request.form.get('verification_id')
                
                if not account_id or not verification_id:
                    user_id_result = "Please provide both Account ID and Verification ID."
                else:
                    query = "SELECT user_id FROM accounts WHERE account_id = %s AND verification_id_no = %s"
                    matching_user_id = execute_query(query, (account_id, verification_id), fetch='one')
                    
                    if matching_user_id:
                        user_id_result = f"{matching_user_id[0]}"
                        app.logger.info(f"User ID retrieved for account: {account_id}")
                    else:
                        user_id_result = "Invalid account details. Please check your information."
                        
            elif recipient_type == 'password':
                user_id = request.form.get('user_id_password')
                account_id = request.form.get('account_id_password')
                
                if not user_id or not account_id:
                    password_result = "Please provide both User ID and Account ID."
                else:
                    query = "SELECT password FROM accounts WHERE account_id = %s AND user_id = %s"
                    matching_password = execute_query(query, (account_id, user_id), fetch='one')
                    
                    if matching_password:
                        password_result = f"{matching_password[0]}"
                        app.logger.info(f"Password retrieved for user: {user_id}")
                    else:
                        password_result = "No matching records found. Please check your information."
                        
        except Exception as e:
            app.logger.error(f"Password/UserID retrieval error: {str(e)}")
            user_id_result = "An error occurred. Please try again."
            password_result = "An error occurred. Please try again."
    
    return render_template("Forgot.html", user_id_result=user_id_result, password_result=password_result)

@app.route('/admin')
def admin():
    return redirect(url_for('admin_details'))

@app.route('/admin_details', methods=['GET'])
def admin_details():
    try:
        # Get all accounts
        account_query = "SELECT * FROM accounts ORDER BY account_id"
        accounts_data = execute_query(account_query, fetch='all')
        
        # Get all loans
        loan_query = "SELECT * FROM loan ORDER BY loan_id"
        loan_data = execute_query(loan_query, fetch='all')
        
        # Get search results if any
        user_data = session.get('search_data')
        app.logger.info(f"Accounts found: {len(accounts_data)}")
        app.logger.info(f"Loans found: {len(loan_data)}")
        if loan_data:
            app.logger.info(f"First loan: {loan_data[0]}")
        return render_template('Admin_Details.html', 
                             user_data=user_data,
                             accounts=accounts_data, 
                             loans=loan_data)
                             
    except Exception as e:
        app.logger.error(f"Admin details error: {str(e)}")
        flash('An error occurred loading admin panel.', 'error')
        return redirect(url_for('index'))

@app.route('/update_loan_status', methods=['POST'])
def update_loan_status():
    try:
        loan_id = request.form.get('loanId')
        new_status = request.form.get('newStatus')
        
        if not loan_id or not new_status:
            return "failure"
        
        update_query = "UPDATE loan SET status = %s WHERE loan_id = %s"
        execute_query(update_query, (new_status, loan_id))
        
        app.logger.info(f"Loan status updated: ID {loan_id}, Status: {new_status}")
        return "success"
        
    except Exception as e:
        app.logger.error(f"Update loan status error: {str(e)}")
        return "failure"

@app.route('/search_user', methods=['POST'])
def search_user():
    try:
        search_query = request.form.get('search_query')
        if not search_query:
            flash('Please enter search criteria.', 'error')
            return redirect(url_for('admin_details'))
        
        # Search by account_id, user_id, or account_holder_name
        query = """
            SELECT * FROM accounts 
            WHERE account_id::text = %s 
               OR user_id::text = %s 
               OR LOWER(account_holder_name) LIKE LOWER(%s)
        """
        search_pattern = f"%{search_query}%"
        account_data = execute_query(query, (search_query, search_query, search_pattern), fetch='all')
        
        session['search_data'] = account_data
        
        if account_data:
            flash(f'Found {len(account_data)} matching record(s).', 'success')
        else:
            flash('No matching records found.', 'error')
        
        return redirect(url_for('admin_details'))
        
    except Exception as e:
        app.logger.error(f"Search user error: {str(e)}")
        flash('An error occurred during search.', 'error')
        return redirect(url_for('admin_details'))

@app.route('/income_tax')
def income_tax():
    return render_template('Income_tax.html')

@app.route('/logout')
def logout():
    user_id = session.get('user_id')
    if user_id:
        app.logger.info(f"User {user_id} logged out")
    
    session.clear()
    return render_template('Logout.html')

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        execute_query("SELECT 1", fetch='one')
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected'
        }), 200
    except Exception as e:
        app.logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 503

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Internal server error: {str(error)}")
    return render_template('500.html'), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify(error="Rate limit exceeded", message=str(e.description)), 429

# Initialize database tables on startup
def init_db():
    """Initialize database tables if they don't exist"""
    try:
        queries = [
            """
            CREATE TABLE IF NOT EXISTS accounts (
                account_id SERIAL PRIMARY KEY,
                user_id INTEGER,
                bank VARCHAR(100),
                account_number VARCHAR(20) UNIQUE,
                account_type_name VARCHAR(100),
                date_of_birth DATE,
                verification_id_no VARCHAR(20) NOT NULL,
                account_holder_name VARCHAR(100) NOT NULL,
                contact_no VARCHAR(15),
                email_id VARCHAR(255),
                address VARCHAR(255),
                password VARCHAR(255) NOT NULL,
                encrypted_password VARCHAR(255),
                account_opening_date DATE NOT NULL,
                balance DECIMAL(10,2) NOT NULL DEFAULT 0.00
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS admin (
                ad_user_id INTEGER PRIMARY KEY,
                ad_name VARCHAR(255) NOT NULL,
                ad_verification_id VARCHAR(255) NOT NULL,
                ad_password VARCHAR(255) NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS loan (
                loan_id SERIAL PRIMARY KEY,
                applicant_name VARCHAR(255) NOT NULL,
                date_of_birth DATE NOT NULL,
                verification_id_no VARCHAR(255),
                contact_no VARCHAR(255),
                email_id VARCHAR(255),
                address VARCHAR(255) NOT NULL,
                job_title VARCHAR(100),
                loan_type VARCHAR(50) NOT NULL,
                loan_amount DECIMAL(10,2) NOT NULL,
                loan_term INTEGER NOT NULL,
                credit_score INTEGER,
                application_date DATE NOT NULL,
                status VARCHAR(20) DEFAULT 'Pending'
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS transaction_history (
                id SERIAL PRIMARY KEY,
                account_id INTEGER NOT NULL,
                user_id VARCHAR(255),
                bank VARCHAR(255),
                transaction_date DATE NOT NULL,
                recipient_name VARCHAR(255),
                transaction_description TEXT NOT NULL,
                recipient_type VARCHAR(255),
                recipient_no VARCHAR(255),
                transaction_amount DECIMAL(10,2) NOT NULL
            );
            """
        ]
        
        for query in queries:
            execute_query(query)
        
        app.logger.info("Database tables initialized successfully")
        
    except Exception as e:
        app.logger.error(f"Database initialization failed: {str(e)}")

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.getenv('FLASK_ENV') != 'production'
    if not debug_mode:
        app.logger.info("Starting production server")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
