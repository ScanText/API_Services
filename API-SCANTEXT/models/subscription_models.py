# models/subscription_models.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base
from datetime import datetime

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    scan_limit = Column(Integer)
    price = Column(Integer)
    duration_days = Column(Integer)
    description = Column(String, nullable=True)
    user_subscriptions = relationship("UserSubscription", back_populates="subscription", cascade="all, delete")

class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime)
    remaining_scans = Column(Integer)
    is_active = Column(Boolean, default=True)
    auto_renew = Column(Boolean, default=False)
    subscription = relationship("Subscription", backref="user_subscriptions", cascade="all, delete")
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)
    payment = relationship("Payment", backref="user_subscription")

