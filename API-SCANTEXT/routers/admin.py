from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from db.database import SessionLocal
from crud import admin_crud
from schemas import admin_schemas
from models import admin_models
from utils.security import verify_password  # 🔑 импорт хеш-проверки

router = APIRouter()

# 📦 Получить доступ к БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ Создание администратора
@router.post("/create", response_model=admin_schemas.AdminUserOut)
def create_admin(admin: admin_schemas.AdminUserCreate, db: Session = Depends(get_db)):
    return admin_crud.create_admin_user(db, admin)

# 🔐 Авторизация администратора
#@router.post("/login", response_model=admin_schemas.AdminUserOut)
#def login_admin(credentials: admin_schemas.AdminLogin, db: Session = Depends(get_db)):
#    admin = admin_crud.get_admin_user_by_username(db, credentials.username)
#    if not admin or not verify_password(credentials.password, admin.password_hash):
#        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
#    return admin


@router.post("/login", response_model=admin_schemas.AdminUserOut)
def login_admin(credentials: admin_schemas.AdminLogin, db: Session = Depends(get_db)):
    print(f"🔐 Попытка входа: {credentials.username}")  # ЛОГ

    admin = admin_crud.get_admin_user_by_username(db, credentials.username)
    if not admin:
        print("❌ Админ не найден в базе")  # ЛОГ
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    if not verify_password(credentials.password, admin.password_hash):
        print("❌ Неверный пароль")  # ЛОГ
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    print(f"✅ Успешный вход: {admin.username}")  # ЛОГ
    return admin


# 📋 Все админы
@router.get("/all", response_model=list[admin_schemas.AdminUserOut])
def get_all_admins(db: Session = Depends(get_db)):
    return admin_crud.get_all_admins(db)

# 📊 Статистика загрузок
@router.get("/{admin_id}/stats")
def get_admin_stats(admin_id: int, db: Session = Depends(get_db)):
    count = db.query(func.count(admin_models.Upload.id)).filter(admin_models.Upload.admin_id == admin_id).scalar()
    return {"upload_count": count}

#
@router.post("/activate-subscription")
def activate_subscription(user_id: int, payment_id: int, db: Session = Depends(get_db)):
    activate_subscription_from_payment(user_id=user_id, payment_id=payment_id, db=db)
    return {"message": "Подписка успешно активирована"}
