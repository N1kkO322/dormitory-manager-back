from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class Duty(Base):
    __tablename__ = "duties"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    floor = Column(Integer, nullable=False)
    completed = Column(Boolean, default=False)
    
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    student = relationship("User", backref="duties")