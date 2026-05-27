import json
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, status
from pydantic import ValidationError
from sqlalchemy import or_
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User
from ..schemas.user import UserCreate, UserResponse, UserUpdate
from ..api.auth import get_current_user
from ..utils.security import get_password_hash
from ..config import settings

router = APIRouter(prefix="/api/users", tags=["users"])
PROFILE_PHOTO_DIR = Path("media/profile_photos")
PROFILE_PHOTO_URL_PREFIX = f"{settings.MEDIA_URL}/profile_photos"
EMPTY_FORM_VALUES = {"", "null", "None", "undefined"}


def require_employee(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "employee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only employees can manage users"
        )

    return current_user


def apply_user_filters(
    query,
    name: str | None,
    group: str | None,
    block: str | None,
    role: str | None,
):
    if name:
        name_filter = f"%{name}%"
        query = query.filter(
            or_(
                User.name.ilike(name_filter),
                User.surname.ilike(name_filter),
                User.middle_name.ilike(name_filter),
            )
        )

    if group:
        query = query.filter(User.group.ilike(f"%{group}%"))

    if block:
        query = query.filter(User.block.ilike(f"%{block}%"))

    if role:
        query = query.filter(User.role == role)

    return query


def get_form_value(value):
    if isinstance(value, str) and value in EMPTY_FORM_VALUES:
        return None

    return value


def parse_emergency_contact(data: dict):
    if "emergency_contact" in data and isinstance(data["emergency_contact"], str):
        emergency_contact = get_form_value(data["emergency_contact"])

        if emergency_contact is None:
            data["emergency_contact"] = None
        else:
            try:
                data["emergency_contact"] = json.loads(emergency_contact)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="emergency_contact must be valid JSON"
                )

    emergency_contact_fields = {
        "name": data.pop("emergency_contact_name", None),
        "phone": data.pop("emergency_contact_phone", None),
        "relation": data.pop("emergency_contact_relation", None),
    }

    if any(value is not None for value in emergency_contact_fields.values()):
        data["emergency_contact"] = emergency_contact_fields


async def parse_user_payload(request: Request, schema):
    content_type = request.headers.get("content-type", "")

    if not content_type.startswith("multipart/form-data"):
        try:
            data = await request.json()
            return schema.model_validate(data), None, False
        except (json.JSONDecodeError, ValidationError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=exc.errors() if hasattr(exc, "errors") else "Invalid JSON body"
            )

    form = await request.form()
    data = {}
    photo_file = None
    photo_deleted = False

    for key, value in form.multi_items():
        if key == "photo":
            if hasattr(value, "filename"):
                if value.filename:
                    photo_file = value
                else:
                    photo_deleted = True
            elif value in EMPTY_FORM_VALUES:
                photo_deleted = True
            continue

        data[key] = get_form_value(value)

    parse_emergency_contact(data)

    try:
        return schema.model_validate(data), photo_file, photo_deleted
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.errors()
        )


def save_profile_photo(photo_file: UploadFile) -> str:
    suffix = Path(photo_file.filename or "").suffix
    filename = f"{uuid4().hex}{suffix}"
    file_path = PROFILE_PHOTO_DIR / filename

    PROFILE_PHOTO_DIR.mkdir(parents=True, exist_ok=True)

    with file_path.open("wb") as destination:
        shutil.copyfileobj(photo_file.file, destination)

    return f"{PROFILE_PHOTO_URL_PREFIX}/{filename}"


def delete_profile_photo(photo_url: str):
    prefix = settings.MEDIA_URL + "/"
    if photo_url and photo_url.startswith(prefix):
        relative_path = photo_url[len(prefix):]
        file_path = Path("media") / relative_path
        try:
            file_path.unlink(missing_ok=True)
        except OSError:
            pass


@router.get("/", response_model=list[UserResponse])
async def get_users(
    name: str | None = Query(default=None),
    group: str | None = Query(default=None),
    block: str | None = Query(default=None),
    role: str | None = Query(default=None),
    role_type: str | None = Query(default=None, alias="type"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _current_user: User = Depends(require_employee),
    db: Session = Depends(get_db)
):
    query = apply_user_filters(db.query(User), name, group, block, role or role_type)
    users = (
        query
        .order_by(User.surname, User.name, User.id)
        .offset(offset)
        .limit(limit)
        .all()
    )
    return users


@router.get("/search", response_model=list[UserResponse])
async def search_users(
    q: str | None = Query(default=None, min_length=1),
    query: str | None = Query(default=None, min_length=1),
    _current_user: User = Depends(require_employee),
    db: Session = Depends(get_db)
):
    search_term = q or query

    if not search_term:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Search query is required"
        )

    search_filter = f"%{search_term}%"
    users = (
        db.query(User)
        .filter(
            or_(
                User.email.ilike(search_filter),
                User.name.ilike(search_filter),
                User.surname.ilike(search_filter),
                User.middle_name.ilike(search_filter),
                User.phone.ilike(search_filter),
                User.group.ilike(search_filter),
                User.block.ilike(search_filter),
                User.room.ilike(search_filter),
            )
        )
        .order_by(User.surname, User.name, User.id)
        .all()
    )
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    _current_user: User = Depends(require_employee),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: Request,
    _current_user: User = Depends(require_employee),
    db: Session = Depends(get_db)
):
    user_data, photo_file, _ = await parse_user_payload(request, UserCreate)

    existing_user = db.query(User).filter(User.email == user_data.email).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )

    if photo_file:
        user_data.photo = save_profile_photo(photo_file)

    emergency_contact = user_data.emergency_contact
    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        role=user_data.role,
        surname=user_data.surname,
        name=user_data.name,
        middle_name=user_data.middle_name,
        phone=user_data.phone,
        photo=user_data.photo,
        group=user_data.group,
        floor=user_data.floor,
        wing=user_data.wing,
        block=user_data.block,
        room=user_data.room,
        room_type=user_data.room_type,
        emergency_contact_name=emergency_contact.name if emergency_contact else None,
        emergency_contact_phone=emergency_contact.phone if emergency_contact else None,
        emergency_contact_relation=emergency_contact.relation if emergency_contact else None,
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    request: Request,
    _current_user: User = Depends(require_employee),
    db: Session = Depends(get_db)
):
    user_data, photo_file, photo_deleted = await parse_user_payload(request, UserUpdate)
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    update_data = user_data.model_dump(exclude_unset=True)

    if "email" in update_data and update_data["email"] != user.email:
        existing_user = db.query(User).filter(User.email == update_data["email"]).first()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )

    password = update_data.pop("password", None)
    if password is not None:
        user.hashed_password = get_password_hash(password)

    if photo_file:
        if user.photo:
            delete_profile_photo(user.photo)
        update_data["photo"] = save_profile_photo(photo_file)
    elif photo_deleted or ("photo" in update_data and update_data["photo"] is None):
        if user.photo:
            delete_profile_photo(user.photo)
        update_data["photo"] = None

    if "emergency_contact" in update_data:
        emergency_contact = update_data.pop("emergency_contact")
        user.emergency_contact_name = emergency_contact["name"] if emergency_contact else None
        user.emergency_contact_phone = emergency_contact["phone"] if emergency_contact else None
        user.emergency_contact_relation = emergency_contact["relation"] if emergency_contact else None

    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    _current_user: User = Depends(require_employee),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    db.delete(user)
    db.commit()
    return {"message": "User deleted"}
