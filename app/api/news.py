from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.news import News
from ..models.user import User
from ..schemas.news import NewsCreate, NewsUpdate, NewsResponse
from ..api.auth import get_current_user
from datetime import datetime

router = APIRouter(prefix="/api/news", tags=["news"])

MONTHS = {
    1: "Января", 2: "Февраля", 3: "Марта", 4: "Апреля",
    5: "Мая", 6: "Июня", 7: "Июля", 8: "Августа",
    9: "Сентября", 10: "Октября", 11: "Ноября", 12: "Декабря"
}

def get_russian_date():
    now = datetime.now()
    month = MONTHS[now.month]
    return now.strftime(f"%d {month} %Y, %H:%M")

@router.get("/", response_model=list[NewsResponse])
async def get_news(db: Session = Depends(get_db)):
    news = db.query(News).order_by(News.id.desc()).all()
    return news

@router.post("/", response_model=NewsResponse)
async def create_news(
    news_data: NewsCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "employee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только сотрудники могут создавать объявления"
        )
    
    news = News(
        type=news_data.type,
        title=news_data.title,
        content=news_data.content,
        priority=news_data.priority,
        author=current_user.name + " " + current_user.surname,
        image_url=news_data.image_url,
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
    news_data: NewsUpdate,
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
    
    update_data = news_data.dict(exclude_unset=True)
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
    
    db.delete(news)
    db.commit()
    return {"message": "Объявление удалено"}