from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from db.database import Base

class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    email = Column(String(100), nullable=False)
    review = Column(String(500), nullable=False)
    service = Column(String(100), nullable=True)
    category = Column(String(20), nullable=False)  # positive, neutral, negative
    date = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="comments")
    
