from pydantic import BaseModel, Field
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

class MachineProblemReport(BaseModel):
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)

class IncorrectInfoReport(BaseModel):
    description: str = Field(min_length=1)
