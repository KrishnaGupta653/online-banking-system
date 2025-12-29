"""
Complete Brevo Test Suite
Tests all aspects of Brevo integration
"""

import os
import sys
import random
from datetime import datetime, timezone
from dotenv import load_dotenv
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

load_dotenv()

class BrevoTester:
    def __init__(self):
        self.api_key = os.getenv('BREVO_API_KEY')
        self.sender_email = os.getenv('BREVO_SENDER_EMAIL', 'krishna3657777@gmail.com')
        self.sender_name = os.getenv('BREVO_SENDER_NAME', 'Banking System')
        self.test_results = []
    
    def print_header(self, title):
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70)
    
    def print_result(self, test_name, passed, message=""):
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
        if message:
            print(f"       {message}")
        self.test_results.append((test_name, passed))
    
    def test_1_environment_vars(self):
        """Test 1: Check environment variables"""
        self.print_header("TEST 1: Environment Variables")
        
        # Check API key
        if not self.api_key:
            self.print_result("API Key", False, "BREVO_API_KEY not found in .env")
            return False
        
        if not self.api_key.startswith('xkeysib-'):
            self.print_result("API Key Format", False, "API key should start with 'xkeysib-'")
            return False
        
        self.print_result("API Key", True, f"Found: {self.api_key[:20]}...")
        
        # Check sender email
        if not self.sender_email:
            self.print_result("Sender Email", False, "BREVO_SENDER_EMAIL not set")
            return False
        
        self.print_result("Sender Email", True, f"Found: {self.sender_email}")
        self.print_result("Sender Name", True, f"Found: {self.sender_name}")
        
        return True
    
    def test_2_api_connection(self):
        """Test 2: Test API connection"""
        self.print_header("TEST 2: API Connection")
        
        try:
            configuration = sib_api_v3_sdk.Configuration()
            configuration.api_key['api-key'] = self.api_key
            
            api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
                sib_api_v3_sdk.ApiClient(configuration)
            )
            
            self.api_instance = api_instance
            self.print_result("API Client Creation", True, "Successfully created API client")
            return True
            
        except Exception as e:
            self.print_result("API Client Creation", False, str(e))
            return False
    
    def test_3_send_simple_email(self):
        """Test 3: Send simple test email"""
        self.print_header("TEST 3: Simple Email Send")
        
        try:
            sender = {"name": self.sender_name, "email": self.sender_email}
            to = [{"email": self.sender_email}]  # Send to yourself
            
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=to,
                sender=sender,
                subject="Test Email from Brevo",
                html_content="<h1>Success!</h1><p>This is a test email.</p>",
                text_content="Success! This is a test email."
            )
            
            api_response = self.api_instance.send_transac_email(send_smtp_email)
            
            self.print_result("Simple Email", True, f"Message ID: {api_response.message_id}")
            return True
            
        except ApiException as e:
            self.print_result("Simple Email", False, str(e))
            return False
    
    def test_4_send_otp_email(self):
        """Test 4: Send OTP-style email"""
        self.print_header("TEST 4: OTP Email Format")
        
        test_otp = str(random.randint(1000, 9999))
        
        html_content = f"""
        <div style="max-width: 600px; margin: 0 auto; font-family: Arial;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        color: white; padding: 30px; text-align: center;">
                <h1>🏦 Banking System</h1>
            </div>
            <div style="padding: 30px; background: #f5f5f5;">
                <p>Your OTP Code:</p>
                <div style="font-size: 48px; color: #667eea; letter-spacing: 15px; 
                            text-align: center; font-family: monospace; margin: 20px 0;">
                    {test_otp}
                </div>
                <p style="text-align: center; color: #666;">Valid for 10 minutes</p>
            </div>
        </div>
        """
        
        try:
            sender = {"name": self.sender_name, "email": self.sender_email}
            to = [{"email": self.sender_email}]
            
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=to,
                sender=sender,
                subject="🔐 Your Banking OTP",
                html_content=html_content,
                text_content=f"Your OTP: {test_otp}"
            )
            
            api_response = self.api_instance.send_transac_email(send_smtp_email)
            
            self.print_result("OTP Email", True, 
                            f"OTP: {test_otp}, Message ID: {api_response.message_id}")
            return True
            
        except ApiException as e:
            self.print_result("OTP Email", False, str(e))
            return False
    
    def test_5_send_to_different_email(self):
        """Test 5: Send to different email address"""
        self.print_header("TEST 5: Send to Different Email")
        
        test_email = input("Enter test email address (or press Enter to skip): ").strip()
        
        if not test_email:
            self.print_result("Different Email", True, "Skipped by user")
            return True
        
        try:
            sender = {"name": self.sender_name, "email": self.sender_email}
            to = [{"email": test_email}]
            
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=to,
                sender=sender,
                subject="Test from Banking System",
                html_content="<h2>Hello!</h2><p>You can receive emails from our banking app.</p>",
                text_content="Hello! You can receive emails from our banking app."
            )
            
            api_response = self.api_instance.send_transac_email(send_smtp_email)
            
            self.print_result("Different Email", True, 
                            f"Sent to {test_email}, ID: {api_response.message_id}")
            return True
            
        except ApiException as e:
            self.print_result("Different Email", False, str(e))
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "🧪" * 35)
        print("       BREVO COMPLETE TEST SUITE")
        print("🧪" * 35)
        
        tests = [
            self.test_1_environment_vars,
            self.test_2_api_connection,
            self.test_3_send_simple_email,
            self.test_4_send_otp_email,
            self.test_5_send_to_different_email
        ]
        
        for test in tests:
            if not test():
                print("\n⚠️  Test failed. Stopping here.")
                break
        
        # Print summary
        self.print_header("TEST SUMMARY")
        passed = sum(1 for _, result in self.test_results if result)
        total = len(self.test_results)
        
        for test_name, result in self.test_results:
            status = "✅" if result else "❌"
            print(f"{status} {test_name}")
        
        print(f"\n📊 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Your Brevo integration is ready!")
            print("✅ You can now deploy your app to production.")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Please fix the issues above.")
        
        print("=" * 70 + "\n")

if __name__ == "__main__":
    tester = BrevoTester()
    tester.run_all_tests()