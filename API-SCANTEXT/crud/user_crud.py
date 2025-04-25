from sqlalchemy.orm import Session
from models import user_models
from schemas.user_schemas import UserLogin, UserOut, UserCreate
from utils.security import verify_password, hash_password
from models.user_models import User
from sqlalchemy.orm import joinedload
from models import subscription_models
from datetime import datetime, timedelta


from models.subscription_models import Subscription, UserSubscription


# 🔐 Создание нового пользователя с хешированием пароля
def create_user(db: Session, user: UserCreate):
    hashed_pw = hash_password(user.password)
    
    # 🆕 Создание пользователя
    db_user = user_models.User(
        login=user.login,
        email=user.email,
        password_hash=hashed_pw
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # 🔍 Получаем подписку "free"
    free_sub = db.query(subscription_models.Subscription).filter_by(name="free").first()
    if not free_sub:
        raise HTTPException(status_code=500, detail="Подписка 'free' не найдена")

    # 📌 Создаём запись в UserSubscription
    new_subscription = subscription_models.UserSubscription(
        user_id=db_user.id,
        subscription_id=free_sub.id,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=free_sub.duration_days),
        remaining_scans=free_sub.scan_limit,
        is_active=True
    )
    db.add(new_subscription)
    db.commit()
    print(f"✅ Подписка создана: user_id={db_user.id}, subscription_id={free_sub.id}, remaining_scans={free_sub.scan_limit}")

    return db_user


def change_password(db: Session, login: str, old_password: str, new_password: str):
    user = get_user_by_login(db, login)
    if not user or not verify_password(old_password, user.password_hash):
        return None
    user.password_hash = hash_password(new_password)
    db.commit()
    return user

def get_user_by_login(db: Session, login: str):
    user = db.query(User).options(
        joinedload(User.uploads),
        joinedload(User.subscriptions).joinedload(UserSubscription.subscription)
    ).filter(User.login == login).first()

    if user:
        active_sub = next((s for s in user.subscriptions if s.is_active), None)
        if active_sub:
            user.subscription_type = active_sub.subscription.name
            user.remaining_scans = active_sub.remaining_scans
        else:
            user.subscription_type = "none"
            user.remaining_scans = 0

    return user

def get_all_users(db: Session):
    return db.query(user_models.User).all()

def delete_user_by_id(db: Session, user_id: int):
    user = db.query(user_models.User).filter(user_models.User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return True
    return False
