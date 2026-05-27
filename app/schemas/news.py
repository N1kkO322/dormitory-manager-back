from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class NewsCreate(BaseModel):
    type: str = "Уведомление"
    title: str
    content: str
    priority: str = "medium"
    author: str = "Администрация"
    image_url: Optional[str] = None

class NewsUpdate(BaseModel):
    type: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    priority: Optional[str] = None
    author: Optional[str] = None 
    image_url: Optional[str] = None

class NewsResponse(BaseModel):
    id: int
    type: str
    title: str
    content: str
    priority: str
    author: str
    image_url: Optional[str] = None
    created: str
    created_at: datetime
    
    class Config:
        from_attributes = True