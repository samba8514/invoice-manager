# fetch_emails.py

from flask import current_app
import os
from models import db, Invoice, FetchLog
from dotenv import load_dotenv
import imaplib
import email
from email.header import decode_header
import hashlib
from datetime import datetime
import platform
import getpass

# ==== CONFIG ====

load_dotenv()

EMAIL = os.getenv("EMAIL_USER")
PASSWORD = os.getenv("EMAIL_PASS")
IMAP_SERVER = 'imap.one.com'
IMAP_PORT = 993
SAVE_FOLDER = os.path.join("invoices")

# ==== Compute SHA256 hash ====
def compute_hash(data):
    return hashlib.sha256(data).hexdigest()

# ==== Connect to IMAP and fetch PDFs ====
def log_action(message):
    from datetime import datetime
    hostname = platform.node()
    system_user = getpass.getuser()
    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.utcnow()}] [{system_user}@{hostname}] {message}\n")

        
def fetch_pdfs():
    os.makedirs(SAVE_FOLDER, exist_ok=True)
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(EMAIL, PASSWORD)
    mail.select("inbox")

    # Search for emails since a given date
    since_date = '01-Mar-2025'
    status, messages = mail.search(None, 'SINCE', since_date)
    email_ids = messages[0].split()

    for email_id in email_ids:
        res, msg_data = mail.fetch(email_id, "(RFC822)")
        if res != 'OK':
            continue

        msg = email.message_from_bytes(msg_data[0][1])
        subject_data = decode_header(msg["Subject"])[0]
        subject, encoding = subject_data[0], subject_data[1]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or 'utf-8', errors='ignore')

        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue

            filename = part.get_filename()
            if filename and filename.lower().endswith(".pdf"):
                raw_data = part.get_payload(decode=True)
                file_hash = compute_hash(raw_data)

                with current_app.app_context():
                    existing = Invoice.query.filter_by(filename=filename).first()
                    duplicate = Invoice.query.filter_by(comment=file_hash).first()
                    if existing or duplicate:
                        print(f"🔁 Duplicate found, skipping: {filename}")
                        continue

                filepath = os.path.join(SAVE_FOLDER, filename)
                with open(filepath, 'wb') as f:
                    f.write(raw_data)
                print(f"📥 Downloaded: {filename}")

                # Add to DB with file hash in comment field (for simplicity)
                with current_app.app_context():
                    new_invoice = Invoice(
                        filename=filename,
                        status="Unpaid",
                        comment=file_hash,
                        uploaded_at=datetime.utcnow()
                    )
                    db.session.add(new_invoice)
                    db.session.commit()
                    print(f"✅ Added to DB: {filename}")
                    log_action(f"Added to DB: {filename}")

    mail.logout()
    # ✅ After all emails processed, log fetch time
    with current_app.app_context():
        db.session.add(FetchLog())
        db.session.commit()
        print("📌 Fetch timestamp saved to DB.")
        
if __name__ == "__main__":
    fetch_pdfs()