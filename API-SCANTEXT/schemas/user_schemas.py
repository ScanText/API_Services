from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, Literal
from schemas.subscription_schemas import SubscriptionShort

class UserBase(BaseModel):
    login: str
    email: str

class UserLogin(BaseModel):
    login: str
    password: str

class UserCreate(BaseModel):
    login: str
    email: EmailStr
    password: str
    subscription_status: Optional[Literal["free", "plus", "premium"]] = "free"

    class Config:
        orm_mode = True

class PasswordChange(BaseModel):
    login: str
    old_password: str
    new_password: str

class UserOut(BaseModel):
    id: int
    login: str
    email: str
    registered_at: datetime
    role: Optional[str] = "user"
    is_blocked: Optional[bool] = False
    active_subscription: Optional[SubscriptionShort] = None

    class Config:
        from_attributes = True

