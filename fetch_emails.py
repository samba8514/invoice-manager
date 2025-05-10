
import imaplib
import email
from email.header import decode_header
from dateutil.relativedelta import relativedelta  # Put at the top of the file
import os
import email.utils 
import hashlib
from datetime import datetime
from dotenv import load_dotenv

# ==== CONFIG ====
load_dotenv()

EMAIL = os.getenv("EMAIL_USER")
PASSWORD = os.getenv("EMAIL_PASS")
BASE_FOLDER = "invoices"

# ==== Compute SHA256 hash ====
def compute_hash(data):
    return hashlib.sha256(data).hexdigest()

# ==== Connect to IMAP and fetch PDFs ====
def fetch_pdfs():
    from app import app, db, Invoice, FetchLog
    from login import log_action
    from pathlib import Path

    mail = imaplib.IMAP4_SSL(os.getenv("IMAP_SERVER"), int(os.getenv("IMAP_PORT")))
    mail.login(EMAIL, PASSWORD)
    mail.select("inbox")
    typ, mailboxes = mail.list()
    print(mailboxes)

    # Search for emails since the start of the current month
    #since_date = (datetime.now().replace(day=1)).strftime('%d-%b-%Y')
    since_date = (datetime.now() - relativedelta(months=3)).strftime('%d-%b-%Y')
    status, messages = mail.uid('search', None, 'SINCE', since_date)
    email_ids = messages[0].split()

    for email_id in email_ids:
        uid = email_id.decode()  # ✅ UID from search result
        print("✅ UID from search:", uid)

        # Now fetch the message body using UID
        res, msg_data = mail.uid('fetch', uid, '(RFC822)')
        if res != 'OK' or not msg_data or not isinstance(msg_data[0], tuple):
            print(f"❌ Failed to fetch message for UID {uid}")
            continue



        msg = email.message_from_bytes(msg_data[0][1])
        subject_data = decode_header(msg["Subject"])[0]
        subject, encoding = subject_data[0], subject_data[1]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or 'utf-8', errors='ignore')
        sender = msg.get("From", "Unknown Sender")

        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue

            filename = Path(part.get_filename()).name
            if filename and filename.lower().endswith(".pdf"):
                raw_data = part.get_payload(decode=True)
                file_hash = compute_hash(raw_data)

                with app.app_context():
                    existing = Invoice.query.filter_by(filename=filename).first()
                    duplicate = Invoice.query.filter_by(comment=file_hash).first()
                    if existing or duplicate:
                        print(f"🔁 Duplicate found, skipping: {filename}")
                        continue

                # Organize files by year/month
                #now = datetime.now()
                #save_folder = os.path.join(BASE_FOLDER, str(now.year), f"{now.month:02}")
                email_date = msg.get("Date")
                parsed_date = email.utils.parsedate_to_datetime(email_date)

                year = str(parsed_date.year)
                month = f"{parsed_date.month:02}"
                relative_path = os.path.join(year, month)
                save_folder = os.path.join(BASE_FOLDER, relative_path)
                os.makedirs(save_folder, exist_ok=True)
                filepath = os.path.join(save_folder, filename)

                with open(filepath, 'wb') as f:
                    f.write(raw_data)
                print(f"📥 Downloaded: {filename} to {save_folder}")

                with app.app_context():
                    new_invoice = Invoice(
                        filename=filename,
                        status="Unpaid",
                        comment=file_hash,
                        uploaded_at=datetime.utcnow(),
                        received_at=parsed_date,
                        imap_uid=uid,
                        subject=subject,
                        sender=sender
                    )
                    new_invoice.filepath = os.path.join(relative_path, filename) 
                    db.session.add(new_invoice)
                    db.session.commit()
                    print(f"✅ Added to DB: {filename}")
                    log_action(f"Added to DB: {filename}")

    mail.logout()
    with app.app_context():
        db.session.add(FetchLog())
        db.session.commit()
        print("📌 Fetch timestamp saved to DB.")

if __name__ == "__main__":
    fetch_pdfs()
