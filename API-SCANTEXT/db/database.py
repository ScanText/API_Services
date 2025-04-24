from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# 📁 Путь к текущей директории (где находится файл database.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 📦 Путь к SQLite-базе данных
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'scantext.db')}"

# 🔌 Подключение к SQLite
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# 🧠 Сессии
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 🏛️ Базовый класс
Base = declarative_base()

# ✅ Зависимость для FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
