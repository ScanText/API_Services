from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UploadOut(BaseModel):
    id: int
    filename: str
    file_url: str
    recognized_text: Optional[str]
    uploaded_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True
