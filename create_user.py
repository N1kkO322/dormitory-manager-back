from app.database import SessionLocal, init_db
from app.models.user import User
from app.utils.security import get_password_hash

def create_user():
    db = SessionLocal()
    
    existing = db.query(User).filter(User.email == "student2@mail.ru").first()
    if existing:
        print("Пользователь уже существует!")
        db.close()
        return
    
    new_user = User(
        email="platon@mail.ru",
        hashed_password=get_password_hash("p"),
        role="student",
        surname="Цветков",
        name="Платон",
        middle_name="Викторович",
        phone="89110215720",
        photo="",
        block="901",
        floor=9,
        wing="male",
        group="ИСТ-212",
        room="901",
        room_type=3,
        emergency_contact_name="Яна Павловна",
        emergency_contact_phone="89119876543",
        emergency_contact_relation="Мама",
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    db.close()
    
    print(f"Создан пользователь: {new_user.name} {new_user.surname}")
    print(f"Email: {new_user.email}")

if __name__ == "__main__":
    init_db()
    create_user()