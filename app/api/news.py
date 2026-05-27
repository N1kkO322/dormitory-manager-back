import json
import os
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from pydantic import ValidationError
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.news import News
from ..models.user import User
from ..schemas.news import NewsCreate, NewsUpdate, NewsResponse
from ..api.auth import get_current_user
from ..config import settings
from datetime import datetime

router = APIRouter(prefix="/api/news", tags=["news"])

NEWS_IMAGE_DIR = Path("media/news_images")
NEWS_IMAGE_URL_PREFIX = f"{settings.MEDIA_URL}/news_images"
EMPTY_FORM_VALUES = {"", "null", "None", "undefined"}

MONTHS = {
    1: "Января", 2: "Февраля", 3: "Марта", 4: "Апреля",
    5: "Мая", 6: "Июня", 7: "Июля", 8: "Августа",
    9: "Сентября", 10: "Октября", 11: "Ноября", 12: "Декабря"
}


def get_russian_date():
    now = datetime.now()
    month = MONTHS[now.month]
    return now.strftime(f"%d {month} %Y, %H:%M")


def get_form_value(value):
    if isinstance(value, str) and value in EMPTY_FORM_VALUES:
        return None
    return value


async def parse_news_payload(request: Request, schema):
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
    image_file = None
    image_deleted = False

    for key, value in form.multi_items():
        if key == "image":
            if hasattr(value, "filename"):
                if value.filename:
                    image_file = value
                else:
                    image_deleted = True
            elif value in EMPTY_FORM_VALUES:
                image_deleted = True
            continue

        data[key] = get_form_value(value)

    try:
        return schema.model_validate(data), image_file, image_deleted
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.errors()
        )


def save_news_image(image_file: UploadFile) -> str:
    suffix = Path(image_file.filename or "").suffix
    filename = f"{uuid4().hex}{suffix}"
    file_path = NEWS_IMAGE_DIR / filename

    NEWS_IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    with file_path.open("wb") as destination:
        shutil.copyfileobj(image_file.file, destination)

    return f"{NEWS_IMAGE_URL_PREFIX}/{filename}"


def delete_news_image(image_url: str):
    prefix = settings.MEDIA_URL + "/"
    if image_url and image_url.startswith(prefix):
        relative_path = image_url[len(prefix):]
        file_path = Path("media") / relative_path
        try:
            file_path.unlink(missing_ok=True)
        except OSError:
            pass


@router.get("/", response_model=list[NewsResponse])
async def get_news(db: Session = Depends(get_db)):
    news = db.query(News).order_by(News.id.desc()).all()
    return news


@router.post("/", response_model=NewsResponse)
async def create_news(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "employee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только сотрудники могут создавать объявления"
        )

    news_data, image_file, _ = await parse_news_payload(request, NewsCreate)

    image_url = news_data.image_url
    if image_file:
        image_url = save_news_image(image_file)

    news = News(
        type=news_data.type,
        title=news_data.title,
        content=news_data.content,
        priority=news_data.priority,
        author=current_user.name + " " + current_user.surname,
        image_url=image_url,
        created=get_russian_date(),
        author_id=current_user.id
    )

    db.add(news)
    db.commit()
    db.refresh(news)
    return news


@router.patch("/{news_id}", response_model=NewsResponse)
async def update_news(
    news_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "employee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только сотрудники могут редактировать объявления"
        )

    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="Объявление не найдено")

    news_data, image_file, image_deleted = await parse_news_payload(request, NewsUpdate)
    update_data = news_data.model_dump(exclude_unset=True)

    if image_file:
        if news.image_url:
            delete_news_image(news.image_url)
        update_data["image_url"] = save_news_image(image_file)
    elif image_deleted or ("image_url" in update_data and update_data["image_url"] is None):
        if news.image_url:
            delete_news_image(news.image_url)
        update_data["image_url"] = None

    for key, value in update_data.items():
        setattr(news, key, value)

    db.commit()
    db.refresh(news)
    return news


@router.delete("/{news_id}")
async def delete_news(
    news_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "employee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только сотрудники могут удалять объявления"
        )

    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="Объявление не найдено")

    if news.image_url:
        delete_news_image(news.image_url)

    db.delete(news)
    db.commit()
    return {"message": "Объявление удалено"}
