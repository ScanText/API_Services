from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PaymentCreate(BaseModel):
    user_id: int
    subscription_id: Optional[int] = None
    amount: int
    method: str
    transaction_id: Optional[str] = None

class PaymentOut(BaseModel):
    id: int
    amount: int
    currency: str
    status: str
    method: str
    transaction_id: Optional[str]
    timestamp: datetime
    subscription_id: Optional[int]

    class Config:
        orm_mode = True
