from pydantic import BaseModel
from typing import Optional

class MachineResponse(BaseModel):
    id: int
    name: str
    status: str
    occupied_by: Optional[str] = None
    occupied_by_id: Optional[int] = None
    occupied_by_role: Optional[str] = None
    occupied_by_block: Optional[str] = None
    occupied_by_room_type: Optional[int] = None
    occupied_at: Optional[str] = None
    
    class Config:
        from_attributes = True

class MachineStatusUpdate(BaseModel):
    status: str 

class MachineCreate(BaseModel):
    name: str