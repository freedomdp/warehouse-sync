import pytz
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.startup_time import StartupTime

class TimeService:
    @staticmethod
    def get_kiev_time():
        """
        Получает текущее время в часовом поясе Киева.
        """
        kiev_tz = pytz.timezone('Europe/Kiev')
        return datetime.now(kiev_tz)

    @staticmethod
    def save_startup_time(db: Session):
        """
        Сохраняет время запуска сервера в базу данных.
        """
        startup_time = StartupTime(id=TimeService.get_kiev_time())
        db.query(StartupTime).delete()
        db.add(startup_time)
        db.commit()

    @staticmethod
    def get_startup_time(db: Session):
        """
        Получает время запуска сервера из базы данных.
        """
        return db.query(StartupTime).first()
