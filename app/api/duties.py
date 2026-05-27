from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from datetime import date, timedelta
from ..database import get_db
from ..models.duty import Duty
from ..models.user import User
from ..schemas.duty import DutyResponse, DutyCreate
from ..api.auth import get_current_user

router = APIRouter(prefix="/api/duties", tags=["duties"])

@router.get("/", response_model=list[DutyResponse])
async def get_duties(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    duties = db.query(Duty).options(joinedload(Duty.student)).all()
    return duties

@router.get("/my", response_model=list[DutyResponse])
async def get_my_duties(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    duties = (
        db.query(Duty)
        .options(joinedload(Duty.student))
        .filter(Duty.student_id == current_user.id)
        .all()
    )
    return duties

@router.get("/today", response_model=list[DutyResponse])
async def get_today_duties(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    today = date.today()
    duties = (
        db.query(Duty)
        .options(joinedload(Duty.student))
        .filter(Duty.date == today)
        .all()
    )
    return duties

@router.get("/week", response_model=list[DutyResponse])
async def get_week_duties(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    today = date.today()
    end_date = today + timedelta(days=7)
    duties = (
        db.query(Duty)
        .options(joinedload(Duty.student))
        .filter(Duty.date >= today, Duty.date <= end_date)
        .order_by(Duty.date)
        .all()
    )
    return duties

@router.post("/", response_model=DutyResponse)
async def create_duty(
    duty_data: DutyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "employee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только сотрудники могут назначать дежурства"
        )
    
    student = db.query(User).filter(User.id == duty_data.student_id).first()
    if not student or student.role != "student":
        raise HTTPException(status_code=404, detail="Студент не найден")
    
    duty = Duty(
        student_id=duty_data.student_id,
        date=duty_data.date,
        floor=duty_data.floor
    )
    
    db.add(duty)
    db.commit()
    db.refresh(duty)
    
    db.refresh(duty, attribute_names=["student"])
    return duty

@router.patch("/{duty_id}/complete", response_model=DutyResponse)
async def complete_duty(
    duty_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    duty = (
        db.query(Duty)
        .options(joinedload(Duty.student))
        .filter(Duty.id == duty_id)
        .first()
    )
    
    if not duty:
        raise HTTPException(status_code=404, detail="Дежурство не найдено")
    
    if duty.student_id != current_user.id and current_user.role != "employee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не можете отметить чужое дежурство"
        )
    
    duty.completed = True
    db.commit()
    db.refresh(duty)
    return duty