import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from ..config import settings
from ..database import get_db
from ..models.user import User
from ..schemas.user import (
    MessageResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    TokenResponse,
    UserLogin,
    UserResponse,
)
from ..utils.email import send_email
from ..utils.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()
logger = logging.getLogger(__name__)

PASSWORD_RESET_MESSAGE = (
    "Если пользователь с таким email существует, письмо для восстановления будет отправлено"
)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный или истекший токен"
        )
    
    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен не содержит ID пользователя"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден"
        )
    
    return user

@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == login_data.email).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Учетная запись отключена"
        )
    
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id}
    )
    
    return TokenResponse(
        access_token=access_token,
        user=user
    )

@router.post(
    "/password-reset/request",
    response_model=MessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def request_password_reset(
    reset_data: PasswordResetRequest,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == reset_data.email).first()
    response = MessageResponse(message=PASSWORD_RESET_MESSAGE)

    if not user or not user.is_active:
        return response

    token = create_access_token(
        data={
            "sub": user.email,
            "user_id": user.id,
            "type": "password_reset",
        },
        expires_delta=timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES),
    )

    reset_link = token
    if settings.FRONTEND_URL:
        reset_link = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?token={token}"

    body = (
        "Здравствуйте!\n\n"
        "Для восстановления пароля DorMan используйте ссылку или токен ниже.\n\n"
        f"{reset_link}\n\n"
        f"Срок действия: {settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} минут.\n"
        "Если вы не запрашивали восстановление пароля, просто проигнорируйте это письмо."
    )

    try:
        send_email(user.email, "Восстановление пароля DorMan", body)
    except Exception:
        logger.exception("Failed to send password reset email")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось отправить письмо для восстановления пароля",
        )

    return response

@router.post("/password-reset/confirm", response_model=MessageResponse)
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db),
):
    payload = decode_access_token(reset_data.token)

    if payload is None or payload.get("type") != "password_reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный или истекший токен восстановления пароля",
        )

    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь не найден или отключен",
        )

    user.hashed_password = get_password_hash(reset_data.new_password)
    db.commit()

    return MessageResponse(message="Пароль успешно изменен")

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
