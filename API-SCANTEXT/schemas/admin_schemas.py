from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AdminLogin(BaseModel):
    username: str
    password: str


class AdminUserBase(BaseModel):
    email: str
    username: str
    subscription_status: Optional[bool] = False


class AdminUserCreate(AdminUserBase):
    password: str


class AdminUserOut(AdminUserBase):
    id: int
    date_registration: datetime
    last_login_date: datetime

    class Config:
        from_attributes = True

# 🔁 Краткая информация о пользователе
class UserShort(BaseModel):
    id: int
    login: str

    class Config:
        from_attributes = True
