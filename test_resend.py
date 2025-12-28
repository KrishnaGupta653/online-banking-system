# test_resend.py
import resend
import os
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.getenv('RESEND_API_KEY')

try:
    result = resend.Emails.send({
        "from": "Banking System <onboarding@resend.dev>",
        "to": "krishna3657777@gmail.com",
        "subject": "Test OTP - Banking System",
        "html": "<h1>Test OTP: 1234</h1><p>If you receive this, Resend is working!</p>"
    })
    print(f"✅ SUCCESS! Email ID: {result.get('id')}")
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
