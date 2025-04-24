import logging

from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, UploadFile, File, Depends, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional, List
import io
from datetime import datetime
import os
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image

# 🔗 Импорт модулей проекта
from routers import user, admin, comment
from db.database import SessionLocal, engine
from crud import admin_crud
from schemas import admin_schemas
from models import admin_models, user_models, comment_models, upload_models, subscription_models
#from models.user_models import Upload, User
from models.user_models import User
from routers import subscription
from routers import upload
from routers import payment
from models.upload_models import Upload


# 🔄 Загрузка переменных окружения (.env)
load_dotenv()

# 🔨 Создание таблиц в БД
admin_models.Base.metadata.create_all(bind=engine)
user_models.Base.metadata.create_all(bind=engine)
comment_models.Base.metadata.create_all(bind=engine)

# 🧠 Инициализация FastAPI
app = FastAPI()

# ✅ Разрешаем доступ с React (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ⚙️ Получение сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 🚀 Подключение маршрутов
app.include_router(user.router, prefix="/user", tags=["User"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(comment.router, prefix="/comments", tags=["Comments"])
app.include_router(upload.router, prefix="/upload", tags=["Uploads"])
app.include_router(subscription.router, prefix="/subscriptions", tags=["Subscriptions"])
app.include_router(payment.router, prefix="/payment", tags=["Payments"])

# Раздача загруженных файлов
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# ✅ Общая функция для сохранения распознанного файла
def save_upload_to_db(db: Session, text: str, image: Image.Image, user: Optional[User] = None) -> Upload:
    os.makedirs("uploads", exist_ok=True)
    filename = f"scan_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jpg"
    filepath = os.path.join("uploads", filename)
    image.save(filepath)

    upload = Upload(
        filename=filename,
        uploaded_at=datetime.utcnow(),
        recognized_text=text,
        file_url=f"http://localhost:8000/uploads/{filename}",
        user_id=user.id if user else None
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return upload

# 🔘 Корневой тест
@app.get("/")
def root():
    return {"message": "👋 Добро пожаловать в ScanText API"}

