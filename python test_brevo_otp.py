# import os
# import random
# from datetime import datetime, timezone
# from dotenv import load_dotenv
# import sib_api_v3_sdk
# from sib_api_v3_sdk.rest import ApiException

# load_dotenv()

# def test_otp_email():
#     """Test the exact OTP email format used in your app"""
    
#     print("=" * 70)
#     print("🔐 BREVO OTP EMAIL TEST - EXACT APP SIMULATION")
#     print("=" * 70)
    
#     # Get credentials
#     api_key = os.getenv('BREVO_API_KEY')
#     sender_email = os.getenv('BREVO_SENDER_EMAIL', 'krishna3657777@gmail.com')
#     sender_name = os.getenv('BREVO_SENDER_NAME', 'Banking System')
    
#     if not api_key:
#         print("❌ BREVO_API_KEY not found in .env")
#         return False
    
#     # Generate test OTP
#     test_otp = str(random.randint(1000, 9999))
#     test_recipient = input("\n📧 Enter email to receive test OTP (or press Enter for default): ").strip()
#     if not test_recipient:
#         test_recipient = sender_email
    
#     print(f"\n📋 Test Details:")
#     print(f"   Sender: {sender_name} <{sender_email}>")
#     print(f"   Recipient: {test_recipient}")
#     print(f"   OTP Code: {test_otp}")
#     print(f"   Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
#     # Create the exact HTML from your app
#     html_content = f"""
# <!DOCTYPE html>
# <html>
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <style>
#         * {{ margin: 0; padding: 0; box-sizing: border-box; }}
#         body {{ 
#             font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
#             line-height: 1.6;
#             background-color: #f5f5f5;
#             padding: 20px;
#         }}
#         .email-container {{
#             max-width: 600px;
#             margin: 0 auto;
#             background-color: #ffffff;
#             border-radius: 12px;
#             overflow: hidden;
#             box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
#         }}
#         .header {{
#             background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#             color: white;
#             padding: 40px 30px;
#             text-align: center;
#         }}
#         .header h1 {{ font-size: 32px; font-weight: 700; margin-bottom: 10px; }}
#         .header p {{ font-size: 16px; opacity: 0.95; }}
#         .content {{ padding: 40px 30px; }}
#         .otp-box {{
#             background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
#             border-radius: 10px;
#             padding: 30px;
#             text-align: center;
#             margin: 30px 0;
#         }}
#         .otp-code {{
#             font-size: 48px;
#             font-weight: bold;
#             color: #667eea;
#             letter-spacing: 15px;
#             font-family: 'Courier New', monospace;
#             margin: 10px 0;
#         }}
#         .footer {{
#             text-align: center;
#             padding: 30px;
#             background-color: #f8f9fa;
#             color: #6c757d;
#             font-size: 13px;
#         }}
#     </style>
# </head>
# <body>
#     <div class="email-container">
#         <div class="header">
#             <h1>🏦 Banking System</h1>
#             <p>Secure Account Verification</p>
#         </div>
#         <div class="content">
#             <p style="font-size: 16px; color: #555;">
#                 You requested an OTP to create a new bank account. 
#                 Please use the code below:
#             </p>
#             <div class="otp-box">
#                 <div style="font-size: 14px; color: #666; margin-bottom: 15px;">YOUR OTP CODE</div>
#                 <div class="otp-code">{test_otp}</div>
#                 <div style="font-size: 14px; color: #666; margin-top: 15px;">⏱️ Valid for 10 minutes</div>
#             </div>
#             <div style="background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; border-radius: 4px;">
#                 <p style="color: #856404; font-size: 14px;">
#                     <strong>⚠️ Important:</strong> This OTP will expire in 10 minutes.
#                 </p>
#             </div>
#         </div>
#         <div class="footer">
#             <p><strong>Banking System</strong></p>
#             <p>© 2024 Banking System. All rights reserved.</p>
#         </div>
#     </div>
# </body>
# </html>
#     """
    
#     text_content = f"""
# Banking System - Your OTP Code

# Your One-Time Password (OTP) is: {test_otp}

# This OTP is valid for 10 MINUTES ONLY.

# If you didn't request this, please ignore this email.

# © 2024 Banking System
#     """
    
#     try:
#         # Configure and send
#         configuration = sib_api_v3_sdk.Configuration()
#         configuration.api_key['api-key'] = api_key
        
#         api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
#             sib_api_v3_sdk.ApiClient(configuration)
#         )
        
#         sender = {"name": sender_name, "email": sender_email}
#         to = [{"email": test_recipient}]
        
#         send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
#             to=to,
#             sender=sender,
#             subject="🏦 Your Banking OTP - Valid for 10 Minutes",
#             html_content=html_content,
#             text_content=text_content
#         )
        
#         print("\n📤 Sending OTP email...")
#         api_response = api_instance.send_transac_email(send_smtp_email)
        
#         print("\n" + "=" * 70)
#         print("✅ SUCCESS! OTP EMAIL SENT!")
#         print("=" * 70)
#         print(f"📧 Message ID: {api_response.message_id}")
#         print(f"🔐 OTP Code: {test_otp}")
#         print(f"📬 Sent to: {test_recipient}")
#         print("\n💡 Check your email now!")
#         print("=" * 70)
        
#         return True
        
#     except ApiException as e:
#         print(f"\n❌ Brevo API Error: {e}")
#         return False
#     except Exception as e:
#         print(f"\n❌ Error: {e}")
#         return False

# if __name__ == "__main__":
#     test_otp_email()
"""
Simple Brevo Email Test
Run this to verify your API key works
"""

import os
from dotenv import load_dotenv
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

# Load environment variables
load_dotenv()

def test_brevo_simple():
    """Simple test to send one email"""
    
    print("=" * 60)
    print("🧪 BREVO EMAIL TEST - SIMPLE VERSION")
    print("=" * 60)
    
    # Get API key from environment
    api_key = os.getenv('BREVO_API_KEY')
    
    if not api_key:
        print("❌ ERROR: BREVO_API_KEY not found in .env file")
        print("Please add: BREVO_API_KEY=xkeysib-your-key")
        return False
    
    print(f"\n✓ API Key found: {api_key[:20]}...")
    
    try:
        # Configure Brevo
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = api_key
        
        # Create API instance
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )
        
        print("✓ Brevo API client configured")
        
        # Email details
        sender_email = os.getenv('BREVO_SENDER_EMAIL', 'krishna3657777@gmail.com')
        test_recipient = 'krishna060503@gmail.com'  # Send to yourself first
        
        sender = {
            "name": "Banking System Test",
            "email": sender_email
        }
        
        to = [{"email": test_recipient}]
        
        # Simple HTML content
        html_content = """
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        color: white; padding: 30px; text-align: center; border-radius: 10px;">
                <h1>🎉 Success!</h1>
                <p style="font-size: 18px;">Brevo is working perfectly!</p>
            </div>
            <div style="padding: 30px; background: #f5f5f5; margin-top: 20px; border-radius: 10px;">
                <h2>✅ Test Results:</h2>
                <ul style="font-size: 16px; line-height: 2;">
                    <li>API Key: Valid</li>
                    <li>Connection: Successful</li>
                    <li>Email Delivery: Working</li>
                </ul>
                <p style="margin-top: 30px; color: #666;">
                    You're ready to send OTP emails in your banking app!
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = """
        SUCCESS! Brevo is working perfectly!
        
        Test Results:
        ✓ API Key: Valid
        ✓ Connection: Successful
        ✓ Email Delivery: Working
        
        You're ready to send OTP emails in your banking app!
        """
        
        # Create email object
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=to,
            sender=sender,
            subject="✅ Brevo Test - Your Banking App is Ready!",
            html_content=html_content,
            text_content=text_content
        )
        
        print(f"✓ Email prepared for: {test_recipient}")
        print("\n📤 Sending test email...")
        
        # Send email
        api_response = api_instance.send_transac_email(send_smtp_email)
        
        print("\n" + "=" * 60)
        print("✅ SUCCESS! Email sent successfully!")
        print("=" * 60)
        print(f"📧 Message ID: {api_response.message_id}")
        print(f"📬 Check your inbox: {test_recipient}")
        print("\n💡 Next Steps:")
        print("   1. Check your email inbox (might take 10-30 seconds)")
        print("   2. Check spam folder if not in inbox")
        print("   3. If received, you're ready to deploy!")
        print("=" * 60)
        
        return True
        
    except ApiException as e:
        print("\n" + "=" * 60)
        print("❌ BREVO API ERROR")
        print("=" * 60)
        print(f"Error: {e}")
        print("\nCommon Issues:")
        print("  • Invalid API key - Check your .env file")
        print("  • API key doesn't have permission - Regenerate in Brevo")
        print("  • Network issue - Check your internet connection")
        print("=" * 60)
        return False
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ UNEXPECTED ERROR")
        print("=" * 60)
        print(f"Error: {e}")
        print("=" * 60)
        return False

if __name__ == "__main__":
    test_brevo_simple()