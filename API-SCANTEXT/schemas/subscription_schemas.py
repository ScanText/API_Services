# schemas/subscription_schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import Literal
from enum import Enum

class SubscriptionBase(BaseModel):
    name: str
    scan_limit: int
    price: int
    duration_days: int
    description: str | None = None

class SubscriptionOut(SubscriptionBase):
    id: int

    class Config:
        orm_mode = True

class SubscriptionShort(BaseModel):
    name: str
    end_date: datetime
    remaining_scans: int

    class Config:
        orm_mode = True

class UserSubscriptionOut(BaseModel):
    id: int
    user_id: int
    subscription_id: int
    start_date: datetime
    end_date: datetime
    remaining_scans: int
    is_active: bool

    class Config:
        orm_mode = True

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"