
from models import db, ActionLog
from flask import session

def log_action(action, invoice_id=None):
    user_id = session.get("user_id")
    log = ActionLog(user_id=user_id, action=action, invoice_id=invoice_id)
    db.session.add(log)
    db.session.commit()