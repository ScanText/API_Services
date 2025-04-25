from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import os
import requests
from db.database import get_db
from models.user_models import User
from models.upload_models import Upload
from schemas.upload_schemas import UploadOut
from models.subscription_models import UserSubscription, Subscription


router = APIRouter()
UPLOAD_FOLDER = "uploads"

@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...), login: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(login=login).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    
    with open(file_path, "wb") as f:
        f.write(await file.read())

    file_url = f"http://localhost:8000/uploads/{filename}"

    upload = Upload(
        filename=filename,
        file_url=file_url,
        user_id=user.id,
        uploaded_at=datetime.utcnow(),
        recognized_text=None
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return {"upload_id": upload.id, "file_url": file_url}

@router.post("/scan")
def scan_image(upload_id: int = Form(...), db: Session = Depends(get_db)):
    upload = db.query(Upload).filter_by(id=upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    user = upload.user  # получаем пользователя через relationship

    # Проверка лимита сканирований
    user_sub = db.query(UserSubscription).filter_by(user_id=user.id, is_active=True).first()
    if not user_sub or user_sub.remaining_scans <= 0:
        raise HTTPException(status_code=403, detail="Лимит сканирований исчерпан")

    user_sub.remaining_scans -= 1

    file_path = os.path.join(UPLOAD_FOLDER, upload.filename)
    with open(file_path, "rb") as f:
        image_bytes = f.read()

    response = requests.post(
    "https://fastapitext.fly.dev/extract-text/",
    files={"file": ("file.jpg", image_bytes)}
)
    text = response.json().get("text", "")
    print("📩 Ответ от OCR API:", response.json())


    upload.recognized_text = text
    db.commit()

    return {
        "recognized_text": text,
        "subscription_type": user_sub.subscription.name,
        "remaining_scans": user_sub.remaining_scans
    }



@router.get("/uploads/by-user", response_model=list[UploadOut])
def get_uploads_by_user(login: str, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(login=login).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    uploads = db.query(Upload).filter_by(user_id=user.id).order_by(Upload.uploaded_at.desc()).all()
    return uploads
