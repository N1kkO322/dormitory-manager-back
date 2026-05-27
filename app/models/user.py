from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from ..database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="student")
    surname = Column(String, nullable=False)
    name = Column(String, nullable=False)
    middle_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    photo = Column(String, nullable=True)
    group = Column(String, nullable=True)
    floor = Column(Integer, nullable=True)
    wing = Column(String, nullable=True)
    block = Column(String, nullable=True)
    room = Column(String, nullable=True)
    room_type = Column(Integer, nullable=True)
    
    emergency_contact_name = Column(String, nullable=True)
    emergency_contact_phone = Column(String, nullable=True)
    emergency_contact_relation = Column(String, nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)