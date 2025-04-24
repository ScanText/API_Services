from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form

from sqlalchemy.orm import Session
from typing import List

from crud import user_crud
from schemas.user_schemas import UserLogin, UserOut, UserCreate
from db.database import SessionLocal
from utils.security import verify_password, hash_password
from models.user_models import User
from schemas.user_schemas import PasswordChange

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
        return db_user
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
@router.get("/", response_model=List[UserOut])
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()

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
    response = requests.post("https://fastapitext.fly.dev/extract-text/", files={"image": ("file.jpg", image_bytes)})
    text = response.json().get("text", "")

    # Обновляем запись
    upload.recognized_text = text
    db.commit()

    return {"recognized_text": text}
