from app.database import SessionLocal, init_db
from app.models.user import User
from app.models.news import News
from app.models.machine import Machine
from app.utils.security import get_password_hash
from datetime import date, timedelta

def seed_users():
    db = SessionLocal()
    
    if db.query(User).count() > 0:
        print("Пользователи уже существуют. Пропускаем.")
        db.close()
        return
    
    users = [
        User(
            email="gleb.nikolaev.1980@mail.ru",
            hashed_password=get_password_hash("q"),
            role="student",
            surname="Николаев",
            name="Глеб",
            middle_name="Сергеевич",
            phone="89115704580",
            block="801",
            floor=8,
            wing="male",
            group="ИСТ-212",
            room="901",
            room_type=3,
            emergency_contact_name="Екатерина Червонцева",
            emergency_contact_phone="89114902370",
            emergency_contact_relation="Мама",
            photo="https://i.pinimg.com/736x/fd/92/b2/fd92b2cd01e556e9463db5f378264c01.jpg"
        ),
        User(
            email="administratorDorm@mail.ru",
            hashed_password=get_password_hash("q"),
            role="employee",
            surname="Петрова",
            name="Анна",
            middle_name="Олеговна",
            phone="89113698721",
            photo="https://sayanogorsk.rhotel.site/storage/L2ltYWdlcy9ob3RlbHMvNzQ4OTUvMjUuanBn"
        ),
    ]
    
    for user in users:
        db.add(user)
    
    db.commit()
    db.close()
    print(f"Добавлено {len(users)} тестовых пользователей")

def seed_news():
    db = SessionLocal()
    
    if db.query(News).count() > 0:
        print("Объявления уже существуют. Пропускаем.")
        db.close()
        return
    
    news_list = [
        News(
            type="Уведомление",
            title="Санитарная проверка",
            content="Уважаемые студенты! 20 мая в 10:00 состоится плановая санитарная проверка комнат. Просьба обеспечить доступ и навести порядок.",
            priority="high",
            author="Администрация",
            image_url=None,
            created="17 мая 2026, 14:30",
            author_id=2
        ),
        News(
            type="Событие",
            title="Общее собрание жильцов",
            content="25 мая в 18:00 в актовом зале общежития состоится общее собрание. Явка всех студентов обязательна. Повестка: правила проживания, подготовка к летнему периоду.",
            priority="medium",
            author="Администрация",
            image_url="https://images.unsplash.com/photo-1577896851231-70ef18881754?w=800",
            created="17 мая 2026, 12:15",
            author_id=2
        ),
    ]
    
    for news in news_list:
        db.add(news)
    
    db.commit()
    db.close()
    print(f"Добавлено {len(news_list)} тестовых объявлений")

def seed_machines():
    db = SessionLocal()
    
    if db.query(Machine).count() > 0:
        print("Машины уже существуют. Пропускаем.")
        db.close()
        return
    
    machines = [
        Machine(name="Стиральная машина №1"),
        Machine(name="Стиральная машина №2"),
        Machine(name="Стиральная машина №3"),
        Machine(name="Стиральная машина №4"),
    ]
    
    for machine in machines:
        db.add(machine)
    
    db.commit()
    db.close()
    print(f"Добавлено {len(machines)} стиральных машин")

def seed_duties():
    from app.models.duty import Duty
    
    db = SessionLocal()
    
    if db.query(Duty).count() > 0:
        print("Дежурства уже существуют. Пропускаем.")
        db.close()
        return
    
    today = date.today()
    duties = [
        Duty(student_id=1, date=today, floor=8),
        Duty(student_id=1, date=today + timedelta(days=2), floor=8),
        Duty(student_id=1, date=today + timedelta(days=4), floor=8),
        Duty(student_id=1, date=today + timedelta(days=6), floor=8),
    ]
    
    for duty in duties:
        db.add(duty)
    
    db.commit()
    db.close()
    print(f"Добавлено {len(duties)} дежурств")

if __name__ == "__main__":
    init_db()
    seed_users()
    seed_news()
    seed_machines()
    seed_duties()
    print("Наполнение базы данных завершено!")