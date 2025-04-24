from sqlalchemy.orm import Session
from schemas import admin_schemas
from models import admin_models
from utils.security import hash_password
from sqlalchemy.orm import joinedload

# 🔐 Создание администратора с хешированием пароля
def create_admin_user(db: Session, admin: admin_schemas.AdminUserCreate):
    hashed_pw = hash_password(admin.password)
    db_admin = admin_models.AdminUser(
        email=admin.email,
        username=admin.username,
        password_hash=hashed_pw,
        subscription_status=admin.subscription_status
    )
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    return db_admin

def get_admin_user_by_username(db: Session, username: str):
    return db.query(admin_models.AdminUser).filter(admin_models.AdminUser.username == username).first()

# 📋 Все админы
def get_all_admins(db: Session):
    return db.query(admin_models.AdminUser).all()


# 📋 Все платежи
def get_payments(db: Session):
    return db.query(admin_models.Payment).options(joinedload(admin_models.Payment.user)).all()

# 📋 Платежи конкретного пользователя
def get_payments_by_user_id(db: Session, user_id: int):
    return db.query(admin_models.Payment).filter(admin_models.Payment.user_id == user_id).all()
