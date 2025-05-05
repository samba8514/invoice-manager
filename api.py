from flask import Blueprint, request, jsonify
from models import db, Invoice
from datetime import datetime

api_bp = Blueprint("api", __name__)

@api_bp.route("/api/bills", methods=["GET"])
def get_bills():
    status_filter = request.args.get("status")
    query = Invoice.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    bills = query.order_by(Invoice.uploaded_at.desc()).all()
    return jsonify([
        {
            "id": b.id,
            "filename": b.filename,
            "status": b.status,
            "comment": b.comment,
            "subject": b.subject,
            "sender": b.sender,
            "uploaded_at": b.uploaded_at.strftime("%Y-%m-%d") if b.uploaded_at else None
        } for b in bills
    ])

@api_bp.route("/api/bills", methods=["POST"])
def add_manual_bill():
    data = request.json
    if not data or not data.get("filename"):
        return jsonify({"error": "filename is required"}), 400

    new_bill = Invoice(
        filename=data["filename"],
        status=data.get("status", "Unpaid"),
        comment=data.get("comment", ""),
        subject=data.get("subject"),
        sender=data.get("sender"),
        uploaded_at=datetime.utcnow()
    )
    db.session.add(new_bill)
    db.session.commit()
    return jsonify({"message": "Bill added", "id": new_bill.id})

@api_bp.route("/api/bills/<int:bill_id>", methods=["PUT"])
def update_bill(bill_id):
    data = request.json
    bill = Invoice.query.get_or_404(bill_id)
    bill.status = data.get("status", bill.status)
    bill.comment = data.get("comment", bill.comment)
    db.session.commit()
    return jsonify({"message": "Bill updated"})
