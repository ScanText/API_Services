from sqlalchemy.orm import Session
from models import user_models
from schemas.user_schemas import UserLogin, UserOut, UserCreate
from utils.security import verify_password, hash_password
from models.user_models import User

# 🔐 Создание нового пользователя с хешированием пароля
def create_user(db: Session, user: UserCreate):
    hashed_pw = hash_password(user.password)
    db_user = user_models.User(
        login=user.login,
        email=user.email,
        password_hash=hashed_pw
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def change_password(db: Session, login: str, old_password: str, new_password: str):
    user = get_user_by_login(db, login)
    if not user or not verify_password(old_password, user.password_hash):
        return None
    user.password_hash = hash_password(new_password)
    db.commit()
    return user

def get_user_by_login(db: Session, login: str):
    return db.query(user_models.User).filter(user_models.User.login == login).first()

def get_all_users(db: Session):
    return db.query(user_models.User).all()

def delete_user_by_id(db: Session, user_id: int):
    user = db.query(user_models.User).filter(user_models.User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return True
    return False
