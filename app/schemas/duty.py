from pydantic import BaseModel
from typing import Optional
from datetime import date

class StudentShortInfo(BaseModel):
    id: int
    name: str
    surname: str
    block: Optional[str] = None
    room: Optional[str] = None
    room_type: Optional[int] = None
    floor: Optional[int] = None
    photo: Optional[str] = None

class DutyResponse(BaseModel):
    id: int
    date: date
    floor: int
    completed: bool
    student_id: int
    student: StudentShortInfo
    
    class Config:
        from_attributes = True

class DutyCreate(BaseModel):
    student_id: int
    date: date
    floor: int