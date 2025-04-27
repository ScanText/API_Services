from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from db.database import get_db
from models.payment_models import Payment
from models.user_models import User
from models.subscription_models import Subscription, UserSubscription
from schemas.payment_schemas import PaymentCreate, PaymentOut
from fastapi.responses import HTMLResponse
from schemas.subscription_schemas import UpdateSubscriptionRequest
from schemas.payment_schemas import PaymentSuccessRequest
from schemas.payment_schemas import CreatePaymentRequest, PaymentOut, ConfirmPaymentRequest
import requests

import uuid

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
        status="pending",
        currency="UAH",
        timestamp=datetime.utcnow()
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    print(f"[PAYMENT CREATED] User ID: {user.id}, Subscription ID: {subscription.id}, Amount: {data.amount} UAH, Status: pending, Transaction ID: {data.transaction_id}")

    return payment

@router.get("/payment-success", response_class=HTMLResponse)
async def payment_success_page(orderId: str):
    print(f"🔗 Перешли на страницу успеха с orderId={orderId}")

    return HTMLResponse(content=f"""
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Спасибо за оплату!</title>
        <style>
            body {{
                background-color: #f0f4f8;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 100vh;
                font-family: Arial, sans-serif;
            }}
            h1 {{
                color: #22c55e;
                font-size: 48px;
                margin-bottom: 20px;
            }}
            p {{
                font-size: 20px;
                color: #4b5563;
            }}
        </style>
    </head>
    <body>
        <h1>✅ Спасибо за оплату!</h1>
        <p>Ваш заказ {orderId} успешно оплачен и подписка активирована.</p>
    </body>
    </html>
    """, status_code=200)

@router.get("/payments/by-user", response_model=List[PaymentOut])
def get_payments_by_user(user_id: int, db: Session = Depends(get_db)):
    print(f"📥 Получен запрос платежей для user_id={user_id}")
    payments = db.query(Payment).filter_by(user_id=user_id).all()
    print(f"🔎 Найдено платежей: {len(payments)}")
    return payments


def activate_subscription_from_payment(user_id: int, payment_id: int, db: Session):
    payment = db.query(Payment).filter_by(id=payment_id).first()
    if not payment:
        print(f"Платёж не найден: payment_id={payment_id}")
        return

    sub = db.query(Subscription).filter_by(id=payment.subscription_id).first()
    if not sub:
        print(f"Подписка не найдена: subscription_id={payment.subscription_id}")
        return

    print(f"Активация подписки: user_id={user_id}, subscription={sub.name}, scans={sub.scan_limit}")

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


@router.post("/success")
async def payment_success_api(data: PaymentSuccessRequest, db: Session = Depends(get_db)):
    print(f"Получен POST для подтверждения оплаты: orderId = {data.orderId}")

    payment = db.query(Payment).filter_by(transaction_id=data.orderId).first()

    if not payment:
        raise HTTPException(status_code=404, detail="Платёж не найден")

    if payment.status == 'success':
        print(f"Платёж уже был успешным ранее: orderId={data.orderId}")
        return {"message": "Платёж уже был подтверждён ранее"}

    # Обновляем платёж
    print(f"Обновляем статус платежа на success для orderId={data.orderId}")
    payment.status = 'success'

    # Активируем подписку
    activate_subscription_from_payment(user_id=payment.user_id, payment_id=payment.id, db=db)

    db.commit()

    return {"message": "Оплата подтверждена, подписка активирована"}

@router.post("/mono-callback")
async def mono_callback(request: Request):
    data = await request.json()
    print("📩 Пришёл callback от Monobank:")
    print(data)  # Просто печатаем весь пришедший JSON

    return {"message": "✅ Callback получен"}


@router.post("/create-payment")
def create_payment(data: CreatePaymentRequest, db: Session = Depends(get_db)):
    print(f"📩 Поступил запрос на создание платежа: {data.dict()}")
    
    reference = f"order-{uuid.uuid4()}"
    print(f"🔑 Сгенерирован reference: {reference}")

    response = requests.post(
        "https://api.monobank.ua/api/merchant/invoice/create",
        headers={"X-Token": 'uTxwJZS40IeHwlzBmz2FkAh-i5UvDx9Lcpe2hQlfTssI'},
        json={
            "amount": data.amount,
            "ccy": 980,
            "redirectUrl": "http://localhost:3000/payment-success",
            "callbackUrl": "https://your-ngrok-url.ngrok-free.app/payment/mono-callback",
            "merchantPaymInfo": {
                "reference": reference,
                "destination": f"Оплата подписки {data.subscription_id}"
            }
        }
    )

    print(f"📡 Ответ от Monobank: {response.status_code}")
    if response.status_code != 200:
        print(f"❌ Ошибка от Monobank: {response.text}")
        raise HTTPException(status_code=400, detail="Ошибка создания счёта в Monobank")

    invoice_data = response.json()

    # Пишем в БД
    print(f"💾 Запись платежа в БД...")
    payment = Payment(
        user_id=data.user_id,
        subscription_id=data.subscription_id,
        amount=data.amount,
        method='monobank',
        transaction_id=reference,
        status='pending'
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    print(f"✅ Платёж записан. ID пользователя: {data.user_id}, Транзакция: {reference}")

    return {"invoice_url": invoice_data["pageUrl"]}



@router.post("/confirm-latest-payment")
def confirm_latest_payment(data: ConfirmPaymentRequest, db: Session = Depends(get_db)):
    payment = (
        db.query(Payment)
        .filter_by(user_id=data.user_id, status='pending')
        .order_by(Payment.timestamp.desc())
        .first()
    )

    if not payment:
        raise HTTPException(status_code=404, detail="Не найден ожидающий платеж")

    payment.status = 'success'
    db.commit()

    # Здесь активируем подписку
    activate_subscription_from_payment(user_id=data.user_id, payment_id=payment.id, db=db)

    return {"message": "Оплата подтверждена и подписка активирована"}


@router.get("/payments/all", response_model=List[PaymentOut])
def get_all_payments(db: Session = Depends(get_db)):
    payments = db.query(Payment).all()
    print(f"🔎 Всего платежей в базе: {len(payments)}")
    return payments
