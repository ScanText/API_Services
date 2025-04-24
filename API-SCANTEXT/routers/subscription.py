from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List

# Импорты моделей и схем
from db.database import get_db
from models.subscription_models import Subscription, UserSubscription
from models.user_models import User
from models.payment_models import Payment
from schemas.subscription_schemas import SubscriptionOut, SubscriptionShort
from schemas.user_schemas import UserOut


router = APIRouter()

@router.get("/", response_model=List[SubscriptionOut])
def get_subscriptions(db: Session = Depends(get_db)):
    return db.query(Subscription).all()

def activate_subscription_from_payment(user_id: int, payment_id: int, db: Session):
    payment = db.query(Payment).filter_by(id=payment_id).first()
    sub = db.query(Subscription).filter_by(id=payment.subscription_id).first()

    db.query(UserSubscription).filter_by(user_id=user_id, is_active=True).update({"is_active": False})

    new_sub = UserSubscription(
        user_id=user_id,
        subscription_id=sub.id,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=sub.duration_days),
        remaining_scans=sub.scan_limit,
        is_active=True,
        payment_id=payment.id
    )
    db.add(new_sub)
    db.commit()

@router.post("/activate-subscription")
def activate_subscription(user_id: int, payment_id: int, db: Session = Depends(get_db)):
    activate_subscription_from_payment(user_id=user_id, payment_id=payment_id, db=db)
    return {"message": "Подписка успешно активирована"}
