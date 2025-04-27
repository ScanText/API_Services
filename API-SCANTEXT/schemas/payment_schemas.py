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
        model_config = {
            "from_attributes": True
        }

class PaymentSuccessRequest(BaseModel):
    orderId: str

class CreatePaymentRequest(BaseModel):

    user_id: int
    subscription_id: int
    amount: int

class ConfirmPaymentRequest(BaseModel):
    user_id: int