from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form

from sqlalchemy.orm import Session
from typing import List

from crud import user_crud
from schemas.user_schemas import UserLogin, UserOut, UserCreate
from db.database import SessionLocal
from db.database import get_db
from utils.security import verify_password, hash_password
from models.user_models import User
from schemas.user_schemas import PasswordChange
import uuid
from datetime import datetime, timedelta
import requests

from models.upload_models import Upload
from models.subscription_models import UserSubscription
from models.subscription_models import Subscription

from schemas.subscription_schemas import SubscriptionStatus
from schemas.subscription_schemas import UpdateSubscriptionRequest


router = APIRouter()

# 🔌 Подключение к БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 🔐 Вход пользователя
@router.post("/login", response_model=UserOut)
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    try:
        db_user = user_crud.get_user_by_login(db, user.login)
        if not db_user or not verify_password(user.password, db_user.password_hash):
            raise HTTPException(status_code=401, detail="Неверный логин или пароль")

        user_sub = (
            db.query(UserSubscription)
            .join(Subscription)
            .filter(UserSubscription.user_id == db_user.id, UserSubscription.is_active == True)
            .first()
        )

        return UserOut(
            id=db_user.id,
            login=db_user.login,
            email=db_user.email,
            role=db_user.role,
            is_blocked=db_user.is_blocked,
            subscription_type=user_sub.subscription.name if user_sub else "none",
            remaining_scans=user_sub.remaining_scans if user_sub else 0
        )

    except Exception as e:
        print("❌ Ошибка при входе:", e)
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.post("/change-password")
def change_password(data: PasswordChange, db: Session = Depends(get_db)):
    # Получаем пользователя по логину
    user = user_crud.get_user_by_login(db, data.login)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Проверяем старый пароль
    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Неверный текущий пароль")

    # Обновляем пароль
    user.password_hash = hash_password(data.new_password)
    db.commit()

    return {"message": "Пароль успешно обновлён"}

@router.post("/register", response_model=UserOut)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Логирование для проверки входных данных
    print(f"Регистрация нового пользователя: {user.login}, {user.email}")

    # Проверка на уникальность логина
    if user_crud.get_user_by_login(db, user.login):
        print(f"Ошибка: Логин {user.login} уже используется.")
        raise HTTPException(status_code=400, detail="Логин уже используется")

    return user_crud.create_user(db, user)

# 📋 Получить всех пользователей (используется в React)
# @router.get("/", response_model=List[UserOut])
# def get_users(db: Session = Depends(get_db)):
#     return db.query(User).all()

@router.get("/", response_model=List[UserOut])
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    result = []
    for user in users:
        active_sub = (
            db.query(UserSubscription)
            .filter_by(user_id=user.id, is_active=True)
            .join(Subscription)
            .first()
        )
        user.subscription_status = active_sub.subscription.name if active_sub else "free"
        result.append(user)
    return result


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    success = user_crud.delete_user_by_id(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return {"message": f"Пользователь с ID {user_id} удалён"}

@router.get("/{user_id}", response_model=UserOut)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user

@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...), login: str = Form(...), db: Session = Depends(get_db)):
    # Находим пользователя
    user = db.query(User).filter_by(login=login).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Сохраняем файл на диск
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = f"uploads/{filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Создаём запись в Upload
    upload = Upload(
        filename=filename,
        file_url=f"http://localhost:8000/uploads/{filename}",
        user_id=user.id,
        recognized_text=None,
        uploaded_at=datetime.utcnow()
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return {"upload_id": upload.id}

@router.post("/scan-image")
def scan_image(upload_id: int, db: Session = Depends(get_db)):
    upload = db.query(Upload).filter_by(id=upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    # Открываем файл
    with open(f"uploads/{upload.filename}", "rb") as f:
        image_bytes = f.read()

    # Отправляем в внешний OCR
    #response = requests.post("https://fastapitext.fly.dev/extract-text/", files={"image": ("file.jpg", image_bytes)})
    response = requests.post("https://fastapitext-black-feather-5039.fly.dev/extract-text/", files={"file": ("file.jpg", image_bytes)})
    print("📩 Ответ от сервера:", response.json())
    print("📦 Ответ:", response.text)
    print(response.headers)

    text = response.json().get("text", "")

    # Обновляем запись
    upload.recognized_text = text
    db.commit()

    return {"recognized_text": text}

@router.get("/user/{user_id}/subscription", response_model=SubscriptionStatus)
def get_user_subscription(user_id: int, db: Session = Depends(get_db)):
    user_sub = db.query(UserSubscription).filter_by(user_id=user_id, is_active=True).first()
    if not user_sub:
        raise HTTPException(status_code=404, detail="Активная подписка не найдена")
    return {
        "subscription_type": user_sub.subscription.name,
        "remaining_scans": user_sub.remaining_scans
    }

@router.get("/subscription-status")
def subscription_status(login: str, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(login=login).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    active_sub = (
    db.query(UserSubscription)
    .join(User)
    .join(Subscription)
    .filter(User.login == login, UserSubscription.is_active == True)
    .first()
    )
    if not active_sub:
        return {"subscription_type": "none", "remaining_scans": 0}

    return {
        "subscription_type": active_sub.subscription.name,
        "remaining_scans": active_sub.remaining_scans
    }

@router.get("/user_info/{login}", response_model=UserOut)
def get_user_info(login: str, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(login=login).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    user_sub = (
        db.query(UserSubscription)
        .join(Subscription)
        .filter(UserSubscription.user_id == user.id, UserSubscription.is_active == True)
        .first()
    )

    return UserOut(
        id=user.id,
        login=user.login,
        email=user.email,
        role=user.role,
        is_blocked=user.is_blocked,
        subscription_type=user_sub.subscription.name if user_sub else "none",
        remaining_scans=user_sub.remaining_scans if user_sub else 0
    )

@router.post("/update-subscription")
def update_user_subscription(data: UpdateSubscriptionRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(login=data.login).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    new_sub = db.query(Subscription).filter_by(name=data.new_status).first()
    if not new_sub:
        raise HTTPException(status_code=404, detail="Подписка не найдена")

    db.query(UserSubscription).filter_by(user_id=user.id, is_active=True).update({"is_active": False})

    new_user_sub = UserSubscription(
        user_id=user.id,
        subscription_id=new_sub.id,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=new_sub.duration_days),
        remaining_scans=new_sub.scan_limit,
        is_active=True
    )
    db.add(new_user_sub)
    db.commit()

    return {"message": f"Подписка пользователя {data.login} обновлена до {data.new_status}"}