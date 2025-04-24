from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from db.database import get_db
from models.payment_models import Payment
from models.user_models import User
from models.subscription_models import Subscription
from schemas.payment_schemas import PaymentCreate, PaymentOut

router = APIRouter()

@router.post("/pay", response_model=PaymentOut)
def make_payment(data: PaymentCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(id=data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    subscription = db.query(Subscription).filter_by(id=data.subscription_id).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    payment = Payment(
        user_id=user.id,
        subscription_id=subscription.id,
        amount=data.amount,
        method=data.method,
        transaction_id=data.transaction_id,
        status="success",
        currency="UAH",
        timestamp=datetime.utcnow()
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment

@router.get("/payments/by-user", response_model=List[PaymentOut])
def get_payments_by_user(user_id: int, db: Session = Depends(get_db)):
    payments = db.query(Payment).filter_by(user_id=user_id).all()
    if not payments:
        raise HTTPException(status_code=404, detail="No payments found for this user")
    return payments
