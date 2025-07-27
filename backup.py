import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
from mysql.connector import pooling
import random
from flask_mail import Mail, Message
import requests
from cryptography.fernet import Fernet
import qrcode
from io import BytesIO
import base64
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__, static_folder='static')
app.secret_key = os.getenv('SECRET_KEY')
mycon = mysql.connector.connect(host=os.getenv('DB_HOST'),
                                 user=os.getenv('DB_USER'),
                                 passwd=os.getenv('DB_PASSWORD'),
                                 database=os.getenv('DB_NAME'))

cursor = mycon.cursor()
key = os.getenv('ENCRYPTION_KEY').encode()
cipher_suite = Fernet(key)
def encrypt_password(password):
    password_bytes = password.encode('utf-8')
    encrypted_password = cipher_suite.encrypt(password_bytes)
    return encrypted_password
def decrypt_password(encrypted_password):
    decrypted_password_bytes = cipher_suite.decrypt(encrypted_password)
    decrypted_password = decrypted_password_bytes.decode('utf-8')
    return decrypted_password
def is_account_number_unique(account_number, cursor):
    query = "SELECT COUNT(*) FROM accounts WHERE account_number = %s"
    cursor.execute(query, (account_number,))
    result = cursor.fetchone()
    return result[0] == 0
def generate_unique_account_number(cursor):
    while True:
        account_number = ''.join(random.choice('0123456789') for _ in range(10))
        if is_account_number_unique(account_number, cursor):
            return account_number
def is_user_id_unique(user_id, cursor):
    query = "SELECT COUNT(*) FROM accounts WHERE user_id = %s"
    cursor.execute(query, (user_id,))
    result = cursor.fetchone()
    return result[0] == 0
def generate_unique_user_id(cursor):
    while True:
        user_id = ''.join(random.choice('0123456789') for _ in range(5))
        if is_user_id_unique(user_id, cursor):
            return user_id
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS').lower() == 'true'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL').lower() == 'true'
mail = Mail(app)
@app.route('/send_otp', methods=['POST'])
def send_otp():
    if request.method == 'POST':
        email = request.form.get('email_id')
        # Generate a random OTP
        # correct_otp = str(random.randint(1000, 9999))
        correct_otp = str(1000)
        session['correct_otp'] = correct_otp
        msg = Message('Your OTP', sender='krishna.gupta3657@gmail.com', recipients=[email])
        msg.body = f'Your OTP is: {correct_otp}'
        try:
            mail.send(msg)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error_message': str(e)}
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        recaptcha_response = request.form.get('g-recaptcha-response')
        secret_key = '6LfgKHcoAAAAAKVgXh274_KxbP0FifwLEXebauPJ' 
        data = {'secret': secret_key,'response': recaptcha_response}
        response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        result = response.json()
        if result['success']:
            user_id= request.form['user_id']
            password = request.form['password']
            query = f"SELECT encrypted_password FROM accounts WHERE user_id = '{user_id}'"
            cursor.execute(query)
            encrypted_passwords = cursor.fetchall() 
            for encrypted_password in encrypted_passwords:
                stored_password = decrypt_password(encrypted_password[0])
                if password == stored_password:
                    return redirect(url_for('account', user_id=user_id))

            return "Login failed. Please check your username and password."
        else:
            return "reCAPTCHA verification failed. Please complete the reCAPTCHA."
    else:
        return "reCAPTCHA verification failed. Please complete the reCAPTCHA."
@app.route('/account/<user_id>')
def account(user_id):
    # Fetch user details
    user_query = f"SELECT user_id, date_of_birth, Verification_id_no, account_holder_name, contact_no FROM accounts WHERE user_id = '{user_id}' LIMIT 1"
    session['user_id']=user_id
    cursor.execute(user_query)
    user_details = cursor.fetchone()
    if user_details:
        user_id = user_details[0]
        date_of_birth = user_details[1]
        Verification_id_no = user_details[2]
        account_holder_name = user_details[3]
        contact_no = user_details[4]
        accounts_query = f"SELECT * FROM accounts WHERE user_id = '{user_id}'"
        cursor.execute(accounts_query)
        accounts_data = cursor.fetchall()
        bank_accounts = []
        total_balance = 0 
        for account_data in accounts_data:
            account_id=account_data[0]
            bank = account_data[2]
            account_number = account_data[3]
            account_type_name = account_data[4]
            password=account_data[11]
            account_opening_date = account_data[13]
            balance = account_data[14]
            bank_account_details = {
                'bank_name': bank,
                'account_id':account_id,
                'account_number': account_number,
                'account_type_name': account_type_name,
                'password':password,
                'account_opening_date': account_opening_date,
                'balance': balance
            }
            bank_accounts.append(bank_account_details)
            session['bank_accounts']=bank_accounts
            total_balance += balance
            transaction_query = f"SELECT * FROM transaction_history WHERE user_id = {user_id}"
            cursor.execute(transaction_query)
            transaction_data = cursor.fetchall()

        return render_template('Account.html', user_id=user_id, date_of_birth=date_of_birth,
                               Verification_id_no=Verification_id_no, account_holder_name=account_holder_name,transaction_data=transaction_data,
                               contact_no=contact_no, bank_accounts=bank_accounts,account_data=account_data,total_balance=total_balance)
    else:
        return "User not found."
@app.route('/new_account')
def new_account():
    return render_template('New_account.html',form=request.form)
@app.route('/create_account', methods=['POST'])
def create_account():
    cursor = mycon.cursor()
    if request.method == 'POST':
        account_type_name = request.form.get('account_type_name')
        date_of_birth=request.form.get('date_of_birth')
        bank=request.form.get('bank')
        Verification_id_no = request.form.get('Verification_id_no')
        account_holder_name = request.form.get('account_holder_name')
        contact_no=request.form.get('contact_no')
        email_id=request.form.get('email_id')
        address=request.form.get('address')
        password = request.form.get('password')
        encrypted_password=encrypt_password(password)
        account_opening_date = request.form.get('account_opening_date')
        balance = request.form.get('balance')
        entered_otp = request.form.get('otp')
        account_number = generate_unique_account_number(cursor)
        session['account_number']=account_number
        correct_otp = session.get('correct_otp')
        check_verification_query = "SELECT user_id FROM accounts WHERE Verification_id_no = %s"
        cursor.execute(check_verification_query, (Verification_id_no,))
        existing_user = cursor.fetchone()
        if existing_user:
            user_id = existing_user[0]
        else:
            user_id = generate_unique_user_id(cursor)
        if entered_otp != correct_otp:
            flash('Invalid OTP. Please try again.','error')
            return render_template('New_account.html', form=request.form) 
        insert_query = "INSERT INTO accounts ( user_id, account_number, bank, account_type_name,date_of_birth , Verification_id_no, account_holder_name,contact_no, email_id,address, password,encrypted_password, account_opening_date, balance) VALUES (%s, %s,%s, %s, %s, %s, %s, %s, %s, %s, %s,%s,%s,%s)"
        values = ( user_id,account_number,bank, account_type_name, date_of_birth, Verification_id_no, account_holder_name, contact_no, email_id, address, password,encrypted_password, account_opening_date, balance)
        cursor.execute(insert_query, values)
        mycon.commit()
        session.pop('correct_otp', None)
        return redirect('/account_created_successfully')
    return render_template('New_account.html')
@app.route('/account_created_successfully')
def account_created_successfully():
    cursor = mycon.cursor()
    query = f"SELECT * FROM accounts ORDER BY account_id DESC LIMIT 1"
    cursor.execute(query)
    account_data = cursor.fetchone()
    if account_data:
        account_id=account_data[0]
        user_id=account_data[1]
        bank=account_data[2]
        account_number = account_data[3]
        account_type_name = account_data[4]
        date_of_birth=account_data[5]
        Verification_id_no=account_data[6]
        account_holder_name = account_data[7]
        contact_no = account_data[8]
        email_id = account_data[9]
        address = account_data[10]
        password = account_data[11]
        account_opening_date = account_data[13]
        balance = account_data[14]
        return render_template('Account_created_successfully.html', account_id=account_id,user_id=user_id,bank=bank,account_number=account_number, account_type_name=account_type_name,date_of_birth=date_of_birth,Verification_id_no=Verification_id_no,
                               account_holder_name=account_holder_name, contact_no=contact_no, email_id=email_id,address=address,password=password,
                               account_opening_date=account_opening_date, balance=balance,account_data=account_data)
    else:
        return "Account not found."
@app.route('/home')
def home():
    return render_template('Home.html')
@app.route('/contacts')
def contacts():
    return render_template('Contact_Us.html')

@app.route('/qr_code')
def qr_code():
    user_id=session.get('user_id')
    cursor = mycon.cursor()
    accounts_query = f"SELECT * FROM accounts WHERE user_id = '{user_id}'"
    cursor.execute(accounts_query)
    user_accounts = cursor.fetchall()
    qr_code_images = []
    for account in user_accounts:
        account_number = account[3]
        bank=account[2]
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
        qr_code_images.append({'image': qr_code_image_data, 'account_number': account_number,'bank':bank})
    return render_template('QR_code.html', qr_code_images=qr_code_images)
@app.route('/make_payment', methods=['GET', 'POST'])
def make_payment():
    user_id = session.get('user_id')
    if request.method == 'POST':
        recipient_name = request.form.get('recipient_name')
        recipient_type = request.form.get('recipient_type')
        recipient_no = request.form.get('recipient_account_number' if recipient_type == 'account' else 'recipient_phone_number')
        transaction_description = request.form.get('transaction_description')
        transaction_date = request.form.get('transaction_date')
        transaction_amount = int(request.form.get('amount'))
        selected_account_id = int(request.form.get('selected_account_id'))
        cursor.execute("SELECT bank FROM accounts WHERE account_id = %s", (selected_account_id,))
        bank = cursor.fetchone()[0]
        cursor.execute("SELECT balance FROM accounts WHERE account_id = %s", (selected_account_id,))
        current_balance = cursor.fetchone()[0]
        if transaction_amount < 0:
            flash('Transaction amount cannot be negative.', 'error')
        else:
            new_balance = current_balance - transaction_amount
            try:
                if new_balance < 0:
                    flash('Insufficient balance!', 'error')
                else:
                    cursor.execute("UPDATE accounts SET balance = %s WHERE account_id = %s", (new_balance, selected_account_id))
                    mycon.commit()
                    insert_query = "INSERT INTO transaction_history (account_id, user_id, bank ,transaction_date, recipient_name, transaction_description, recipient_type, recipient_no, transaction_amount) VALUES (%s, %s,%s,%s,%s, %s, %s, %s, %s)"
                    values = (selected_account_id, user_id, bank, transaction_date, recipient_name, transaction_description, recipient_type, recipient_no, transaction_amount)
                    cursor.execute(insert_query, values)
                    mycon.commit()
                    flash('Payment successful!', 'success')
                    return redirect(url_for('account', user_id=user_id))
            except Exception as e:
                flash(f'An error occurred while processing the payment: {str(e)}', 'error')
                print(str(e))
    return render_template('Payment.html')

@app.route('/payment_and_transfer', methods=['GET', 'POST'])
def payment_and_transfer():
     bank_accounts = session.get('bank_accounts')
     return render_template('Payment.html',user_accounts=bank_accounts)

@app.route('/apply_loan', methods=['GET', 'POST'])
def apply_loan():
    if request.method == 'POST':
        # Get form data
        applicant_name = request.form.get('applicant_name')
        date_of_birth = request.form.get('date_of_birth')
        Verification_id_no = request.form.get('Verification_id_no')
        contact_no= request.form.get('contact_no')
        email_id  = request.form.get('email_id ')
        address = request.form.get('address')
        job_title = request.form.get('job_title')
        loan_type = request.form.get('loan_type')
        loan_amount = request.form.get('loan_amount')
        loan_term = request.form.get('loan_term')
        credit_score = request.form.get('credit_score')
        application_date = request.form.get('application_date')
        insert_query = """
            INSERT INTO loan (applicant_name, date_of_birth,Verification_id_no, contact_no,email_id ,address, job_title, loan_type, loan_amount, loan_term, credit_score, application_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s, %s)
        """
        values = (applicant_name, date_of_birth, Verification_id_no,contact_no,email_id ,address, job_title, loan_type, loan_amount, loan_term, credit_score, application_date)
        cursor.execute(insert_query, values)
        mycon.commit()
        return redirect(url_for('loan_app_suc'))
    return render_template('Loan_Apply.html')
@app.route('/loan_app_suc')
def loan_app_suc():
    cursor = mycon.cursor()
    query = f"SELECT * FROM loan ORDER BY loan_id DESC LIMIT 1"
    cursor.execute(query)
    account_data = cursor.fetchone()
    if account_data:
        loan_id=account_data[0]
        applicant_name = account_data[1]
        date_of_birth=account_data[2]
        Verification_id_no=account_data[3]
        contact_no = account_data[4]
        email_id = account_data[5]
        address = account_data[6]
        job_title=account_data[7]
        loan_type=account_data[8]
        loan_amount=account_data[9]
        loan_term=account_data[10]
        credit_score=account_data[11]
        applicant_date=account_data[12]
        status = account_data[13]
        return render_template('Loan_app_suc.html',loan_id=loan_id,applicant_name =applicant_name,date_of_birth=date_of_birth,
                               Verification_id_no=Verification_id_no ,contact_no =contact_no,email_id=email_id ,address=address,job_title=job_title,
                                loan_type=loan_type,loan_amount=loan_amount,loan_term=loan_term,credit_score=credit_score,applicant_date=applicant_date,status =status ,account_data=account_data)
        #return render_template('Account.html', account_number=account_number, account_type_name=account_type_name,account_holder_name=account_holder_name,contact_no=contact_no,email_id=email_id, account_opening_date=account_opening_date, balance=balance, account_data=account_data)
    else:
        return "Status not found."
@app.route('/view_loan_status',methods=["GET", "POST"])
def view_loan_status():
    if request.method == "POST":
        loan_id = request.form["loan_id"]
        # Query the database to get the loan status
        query=cursor.execute("SELECT * FROM loan WHERE loan_id = %s", (loan_id,))
        cursor.execute(query)
        account_data = cursor.fetchone()
        if account_data:
            loan_id=account_data[0]
            applicant_name = account_data[1]
            contact_no = account_data[4]
            email_id = account_data[5]
            loan_type=account_data[8]
            loan_amount=account_data[9]
            loan_term=account_data[10]
            applicant_date=account_data[12]
            status = account_data[13]
            return render_template("View_loan_status.html", loan_id=loan_id ,applicant_name =applicant_name,
                             contact_no =contact_no,email_id=email_id , loan_type=loan_type,loan_amount=loan_amount,loan_term=loan_term,applicant_date=applicant_date,status =status,account_data=account_data)
        else:
            return "Loan ID not found"
    return render_template("View_loan_status.html", loan_id=None, status=None)
@app.route('/forgot')
def forgot():
    return render_template('Forgot.html')
@app.route('/forgotten', methods=['POST','GET'])
def forgotten():
    user_id_result = ""
    password_result = ""
    if request.method == 'POST':
        recipient_type = request.form.get('option')
        try:
            if recipient_type == 'user_id':
                account_id = request.form.get('account_id_user')
                verification_id = request.form.get('verification_id')
                query = "SELECT user_id FROM accounts WHERE account_id = %s AND Verification_id_no = %s"
                cursor.execute(query, (account_id, verification_id))
                matching_user_id = cursor.fetchone()
                if matching_user_id:
                    print(matching_user_id[0])
                    user_id_result = f"{matching_user_id[0]}"
                else:
                    user_id_result = "Invalid account details. Please check your information."
            if recipient_type == 'password':
                user_id = request.form.get('user_id_password')
                account_id = request.form.get('account_id_password')
                # Query the database to check if the provided User ID and Account ID match any of the user's accounts for password retrieval.
                query = "SELECT password FROM accounts WHERE account_id = %s AND user_id = %s"
                cursor.execute(query, (account_id, user_id))
                matching_password = cursor.fetchone()
                if matching_password is not None:
                    password_result = f"{matching_password[0]}"
                else:
                     password_result = "No matching records found for the provided information. Please check your information."
        except Exception as e:
            # Log the error and return an error message
            app.logger.error(f"Error in retrieve_credentials route: {str(e)}")
            print(f"Error in retrieve_credentials route: {str(e)}")
    return render_template("Forgot.html",user_id_result=user_id_result,password_result=password_result)
@app.route('/admin')
def admin():
    # return render_template('Admin_Details.html')
    return redirect(url_for('admin_details'))
# @app.route('/admin_login', methods=['POST'])
# def admin_login():
#     username = request.form.get('admin_user_id')
#     password = request.form.get('admin_password')
#     query = f"SELECT ad_password FROM admin WHERE ad_user_id = '{username}'"
#     cursor.execute(query)
#     ad_password = cursor.fetchall()

#     for passwords in ad_password:
#         stored_password = passwords[0]

#         if password == stored_password:
#             return redirect(url_for('admin_details'))
#         else:
#             return jsonify({"status": "failure"})
#     return render_template('Login.html')

# Route for displaying user details
@app.route('/admin_details', methods=['GET'])
def admin_details():
    account_data=None
    # account_query = "SELECT account_id, user_id, bank, account_number, account_type_name, date_of_birth, verification_id_no, account_holder_name, contact_no, email_id, address, password, balance FROM accounts"
    account_query = "SELECT * FROM accounts"
    cursor.execute(account_query)
    accounts_data = cursor.fetchall()
    loan_query = "SELECT * FROM loan"
    cursor.execute(loan_query)
    loan_data = cursor.fetchall()
    data=session.get('data')
    if data:
       user_data=data
    else:
        user_data=None
    return render_template('Admin_Details.html', user_data=user_data,accounts=accounts_data, loans=loan_data)
   
@app.route('/update_loan_status', methods=['POST'])
def update_loan_status():
    loan_id = request.form.get('loanId')
    new_status = request.form.get('newStatus')
    try:
        update_query = f"UPDATE loan SET status = '{new_status}' WHERE loan_id = {loan_id}"
        cursor.execute(update_query)
        mycon.commit()
        return "success"
    except Exception as e:
        print(e)
        mycon.rollback()
        return "failure"
@app.route('/search_user', methods=['POST'])
def search_user():
    search_query = request.form.get('search_query')
    account_query = f"SELECT * FROM accounts WHERE account_id = %s"
    cursor.execute(account_query, (search_query,))
    account_data = cursor.fetchall()
    session['data']=account_data
    if account_data:
        # If a matching user is found, render a page to display their details
        return redirect(url_for('admin_details'))
    else:
        # Handle the case when no matching user is found
        flash('Invalid Account_id')
        return redirect(url_for('admin_details'))
@app.route('/income_tax')
def income_tax():
    return render_template('Income_tax.html')
@app.route('/logout')
def logout():
    return render_template('Logout.html')



if __name__ == "__main__":
    app.run(debug=True, port=8000)  # Use a different port like 5000

