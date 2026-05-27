from pydantic import AliasChoices, BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class EmergencyContact(BaseModel):
    name: str
    phone: str
    relation: str

class UserCreate(BaseModel):
    email: str
    password: str
    role: str = Field(
        default="student",
        validation_alias=AliasChoices("role", "type"),
    )
    surname: str
    name: str
    middle_name: Optional[str] = None
    phone: Optional[str] = None
    photo: Optional[str] = None
    group: Optional[str] = None
    floor: Optional[int] = None
    wing: Optional[str] = None
    block: Optional[str] = None
    room: Optional[str] = None
    room_type: Optional[int] = None
    emergency_contact: Optional[EmergencyContact] = None

class UserUpdate(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("role", "type"),
    )
    surname: Optional[str] = None
    name: Optional[str] = None
    middle_name: Optional[str] = None
    phone: Optional[str] = None
    photo: Optional[str] = None
    group: Optional[str] = None
    floor: Optional[int] = None
    wing: Optional[str] = None
    block: Optional[str] = None
    room: Optional[str] = None
    room_type: Optional[int] = None
    emergency_contact: Optional[EmergencyContact] = None
    is_active: Optional[bool] = None

class UserLogin(BaseModel):
    email: str
    password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=6)

class MessageResponse(BaseModel):
    message: str

class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    surname: str
    name: str
    middle_name: Optional[str] = None
    phone: Optional[str] = None
    photo: Optional[str] = None
    group: Optional[str] = None
    floor: Optional[int] = None
    wing: Optional[str] = None
    block: Optional[str] = None
    room: Optional[str] = None
    room_type: Optional[int] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
