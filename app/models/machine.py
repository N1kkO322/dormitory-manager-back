from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class Machine(Base):
    __tablename__ = "machines"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    status = Column(String, default="free")
    
    occupied_by = Column(String, nullable=True)
    occupied_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    occupied_by_role = Column(String, nullable=True)
    occupied_by_block = Column(String, nullable=True)
    occupied_by_room_type = Column(Integer, nullable=True)
    occupied_at = Column(String, nullable=True)
    
    user = relationship("User", backref="machines")