import psycopg2
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def create_postgres_tables():
    """Create PostgreSQL tables equivalent to MySQL structure"""
    
    postgres_queries = [
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
    
    return postgres_queries

def migrate_data():
    """Migrate data from MySQL to PostgreSQL"""
    
    # MySQL connection
    mysql_conn = mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        database=os.getenv('MYSQL_DATABASE', 'bank')
    )
    mysql_cursor = mysql_conn.cursor()
    
    # PostgreSQL connection
    postgres_conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        database=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        port=os.getenv('POSTGRES_PORT', 5432)
    )
    postgres_cursor = postgres_conn.cursor()
    
    try:
        # Create tables first
        postgres_queries = create_postgres_tables()
        for query in postgres_queries:
            postgres_cursor.execute(query)
        postgres_conn.commit()
        print("✅ PostgreSQL tables created successfully")
        
        # Migrate accounts table
        mysql_cursor.execute("SELECT * FROM accounts")
        accounts_data = mysql_cursor.fetchall()
        
        for account in accounts_data:
            postgres_cursor.execute("""
                INSERT INTO accounts (
                    account_id, user_id, bank, account_number, account_type_name,
                    date_of_birth, verification_id_no, account_holder_name,
                    contact_no, email_id, address, password, encrypted_password,
                    account_opening_date, balance
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (account_number) DO NOTHING
            """, account)
        
        # Migrate admin table
        mysql_cursor.execute("SELECT * FROM admin")
        admin_data = mysql_cursor.fetchall()
        
        for admin in admin_data:
            postgres_cursor.execute("""
                INSERT INTO admin (ad_user_id, ad_name, ad_verification_id, ad_password)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (ad_user_id) DO NOTHING
            """, admin)
        
        # Migrate loan table
        mysql_cursor.execute("SELECT * FROM loan")
        loan_data = mysql_cursor.fetchall()
        
        for loan in loan_data:
            postgres_cursor.execute("""
                INSERT INTO loan (
                    loan_id, applicant_name, date_of_birth, verification_id_no,
                    contact_no, email_id, address, job_title, loan_type,
                    loan_amount, loan_term, credit_score, application_date, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, loan)
        
        # Migrate transaction_history table
        mysql_cursor.execute("SELECT * FROM transaction_history")
        transaction_data = mysql_cursor.fetchall()
        
        for transaction in transaction_data:
            postgres_cursor.execute("""
                INSERT INTO transaction_history (
                    account_id, user_id, bank, transaction_date, recipient_name,
                    transaction_description, recipient_type, recipient_no, transaction_amount
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, transaction)
        
        postgres_conn.commit()
        print("✅ Data migration completed successfully")
        
        # Update sequences for SERIAL columns
        postgres_cursor.execute("SELECT setval('accounts_account_id_seq', (SELECT MAX(account_id) FROM accounts));")
        postgres_cursor.execute("SELECT setval('loan_loan_id_seq', (SELECT MAX(loan_id) FROM loan));")
        postgres_conn.commit()
        print("✅ Sequences updated successfully")
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        postgres_conn.rollback()
    
    finally:
        mysql_cursor.close()
        mysql_conn.close()
        postgres_cursor.close()
        postgres_conn.close()

if __name__ == "__main__":
    print("🚀 Starting database migration from MySQL to PostgreSQL...")
    migrate_data()
    print("✅ Migration process completed!")