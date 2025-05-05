from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash
from flask_sqlalchemy import SQLAlchemy
from models import db, User, Invoice, FetchLog,ActionLog
from api import api_bp
import os
from datetime import datetime
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from log_utils import log_action

# ==== Setup ====
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///users.db')
app.config['UPLOAD_FOLDER'] = 'invoices'
db.init_app(app)

# ==== Login Required Decorator ====
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ==== Routes ====
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    invoices = Invoice.query.order_by(Invoice.uploaded_at.desc()).all()
    last_log = FetchLog.query.order_by(FetchLog.timestamp.desc()).first()
    return render_template('dashboard.html', invoices=invoices, last_fetched=last_log.timestamp if last_log else None)

@app.route('/fetch-emails')
def fetch_emails_route():
    from fetch_emails import fetch_pdfs
    fetch_pdfs()
    flash("Emails fetched successfully!", "success")
    return redirect(url_for('dashboard'))

@app.route('/upload', methods=['POST'])
@login_required
def upload():
    file = request.files['file']
    if file and file.filename.endswith('.pdf'):
        path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(path)
        new_invoice = Invoice(filename=file.filename)
        db.session.add(new_invoice)
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/update/<int:invoice_id>', methods=['POST'])
@login_required
def update(invoice_id):
    invoice = Invoice.query.get(invoice_id)
    if invoice:
        invoice.status = request.form.get('status')
        invoice.comment = request.form.get('comment')
        db.session.commit()
        log_action(f"Status updated to {invoice.status}", invoice.id)

    return redirect(url_for('dashboard'))

@app.route('/invoices/<path:filename>')
@login_required
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/logs')
@login_required
def view_logs():
    logs = ActionLog.query.order_by(ActionLog.timestamp.desc()).limit(100).all()
    return render_template('logs.html', logs=logs)


# ==== Run ====
if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.register_blueprint(api_bp)
    with app.app_context():
        db.create_all()
    app.run(debug=True)
