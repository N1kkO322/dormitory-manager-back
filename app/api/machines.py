import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..config import settings
from ..database import get_db
from ..models.machine import Machine
from ..models.user import User
from ..schemas.machine import (
    IncorrectInfoReport,
    MachineCreate,
    MachineProblemReport,
    MachineResponse,
    MachineStatusUpdate,
)
from ..schemas.user import MessageResponse
from ..api.auth import get_current_user
from ..utils.email import send_email

router = APIRouter(prefix="/api/machines", tags=["machines"])
logger = logging.getLogger(__name__)

@router.get("/", response_model=list[MachineResponse])
async def get_machines(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    machines = db.query(Machine).order_by(Machine.id).all()
    return machines

@router.post("/", response_model=MachineResponse)
async def create_machine(
    machine_data: MachineCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "employee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только сотрудники могут добавлять машины"
        )
    
    machine = Machine(
        name=machine_data.name,
        status="free"
    )
    
    db.add(machine)
    db.commit()
    db.refresh(machine)
    return machine

@router.post(
    "/report-problem",
    response_model=MessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def report_machine_problem(
    report_data: MachineProblemReport,
    current_user: User = Depends(get_current_user),
):
    recipient_email = settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME
    if not recipient_email:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email для получения сообщений о проблемах не настроен",
        )

    reporter = f"{current_user.surname} {current_user.name}".strip()
    body = (
        "Сообщение о проблеме со стиральной машиной\n\n"
        f"Машина: {report_data.name}\n"
        f"Описание проблемы: {report_data.description}\n\n"
        f"Отправитель: {reporter}\n"
        f"Email отправителя: {current_user.email}"
    )

    try:
        send_email(
            recipient_email,
            "Проблема со стиральной машиной DorMan",
            body,
        )
    except Exception:
        logger.exception("Failed to send machine problem report email")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось отправить сообщение о проблеме",
        )

    return MessageResponse(message="Сообщение о проблеме отправлено")

@router.post(
    "/report-incorrect-info",
    response_model=MessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def report_incorrect_info(
    report_data: IncorrectInfoReport,
    current_user: User = Depends(get_current_user),
):
    recipient_email = settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME
    if not recipient_email:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email для получения сообщений о некорректной информации не настроен",
        )

    reporter = f"{current_user.surname} {current_user.name}".strip()
    body = (
        "Сообщение о некорректности информации\n\n"
        f"Описание: {report_data.description}\n\n"
        f"Отправитель: {reporter}\n"
        f"Email отправителя: {current_user.email}"
    )

    try:
        send_email(
            recipient_email,
            "Некорректная информация DorMan",
            body,
        )
    except Exception:
        logger.exception("Failed to send incorrect info report email")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось отправить сообщение о некорректной информации",
        )

    return MessageResponse(message="Сообщение о некорректной информации отправлено")

@router.patch("/{machine_id}", response_model=MachineResponse)
async def update_machine_status(
    machine_id: int,
    status_update: MachineStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    
    if not machine:
        raise HTTPException(status_code=404, detail="Машина не найдена")
    
    if machine.status == "broken" and status_update.status != "free":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Машина неисправна, обратитесь к администрации"
        )
    
    if status_update.status == "busy":
        if machine.status == "busy":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Машина уже занята"
            )
        
        machine.status = "busy"
        machine.occupied_by = f"{current_user.surname} {current_user.name}"
        machine.occupied_by_id = current_user.id
        machine.occupied_by_role = current_user.role
        machine.occupied_by_block = current_user.block
        machine.occupied_by_room_type = current_user.room_type
        machine.occupied_at = datetime.now().strftime("%d.%m.%Y, %H:%M")
    
    elif status_update.status == "free":
        if machine.status == "broken":
            if current_user.role != "employee":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Только сотрудники могут починить машину"
                )
            machine.status = "free"
            machine.occupied_by = None
            machine.occupied_by_id = None
            machine.occupied_by_role = None
            machine.occupied_by_block = None
            machine.occupied_by_room_type = None
            machine.occupied_at = None
        else:
            if machine.status != "busy":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Машина уже свободна"
                )
            
            if machine.occupied_by_id != current_user.id and current_user.role != "employee":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Вы не можете освободить чужую машину"
                )
            
            machine.status = "free"
            machine.occupied_by = None
            machine.occupied_by_id = None
            machine.occupied_by_role = None
            machine.occupied_by_block = None
            machine.occupied_by_room_type = None
            machine.occupied_at = None
    
    elif status_update.status == "broken":
        if current_user.role != "employee":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Только сотрудники могут отметить машину как сломанную"
            )
        machine.status = "broken"
        machine.occupied_by = None
        machine.occupied_by_id = None
        machine.occupied_by_role = None
        machine.occupied_by_block = None
        machine.occupied_by_room_type = None
        machine.occupied_at = None
    
    db.commit()
    db.refresh(machine)
    return machine

@router.delete("/{machine_id}")
async def delete_machine(
    machine_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "employee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только сотрудники могут удалять машины"
        )
    
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Машина не найдена")
    
    db.delete(machine)
    db.commit()
    return {"message": "Машина удалена"}
