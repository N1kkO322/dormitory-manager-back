from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class News(Base):
    __tablename__ = "news"
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, default="Уведомление")
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    priority = Column(String, default="medium")
    author = Column(String, default="Администрация")
    image_url = Column(String, nullable=True)
    created = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    author_user = relationship("User", backref="news")