from db.database import Base, engine

print("🛠 Создание таблиц...")
Base.metadata.create_all(bind=engine)
print("✅ База данных создана.")
