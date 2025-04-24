from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CommentCreate(BaseModel):
    user_id: int
    email: str
    review: str
    service: str
    category: str

class CommentOut(CommentCreate):
    id: int
    review: str
    category: str
    service: Optional[str]
    date: datetime

    class Config:
        from_attributes = True

