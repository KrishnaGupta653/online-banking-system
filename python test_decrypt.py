import os
import psycopg2
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Load .env values
load_dotenv()

DATABASE_URL = 'postgresql://postgres:Kg653%40postgre@localhost:5432/bank'
ENCRYPTION_KEY = b'Bc0TG0ffA8HHhFBVnYZfsGy5sU7IXipXBprTBzvoxXk='

if not DATABASE_URL:
    print("❌ DATABASE_URL is missing in your .env")
    exit()
if not ENCRYPTION_KEY:
    print("❌ ENCRYPTION_KEY is missing in your .env")
    exit()

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Ask for user ID and password
    user_id = input("Enter user_id to test: ")
    entered_password = input("Enter the password you are trying to log in with: ")

    cur.execute("SELECT password, encrypted_password FROM accounts WHERE user_id = %s;", (user_id,))
    row = cur.fetchone()

    if not row:
        print(f"No account found with user_id: {user_id}")
    else:
        plain_password, encrypted_password = row
        print(f"DB plain password: {plain_password}")
        print(f"DB encrypted password: {encrypted_password}")

        if encrypted_password:
            try:
                fernet = Fernet(ENCRYPTION_KEY)
                decrypted = fernet.decrypt(encrypted_password.encode()).decode('utf-8')
                print(f"Decrypted password: {decrypted}")

                if decrypted == entered_password:
                    print("✅ Login would succeed using encrypted_password")
                else:
                    print("❌ Encrypted password does not match the entered password")
            except Exception as e:
                print(f"❌ Failed to decrypt encrypted_password: {e}")
        elif plain_password:
            if plain_password == entered_password:
                print("✅ Login would succeed using plain password")
            else:
                print("❌ Plain password does not match the entered password")
        else:
            print("No password data found for this account.")

except Exception as db_error:
    print(f"Database error: {db_error}")
