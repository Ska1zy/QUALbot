from pathlib import Path
import json
import random
import string
from aiogram.types import FSInputFile

BASE_DIR = Path(__file__).resolve().parent
USERS_FILE = BASE_DIR / "data" / "users.json"
ALPHABET = string.ascii_letters + string.digits

def load_users():
    if not USERS_FILE.exists():
        USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        return {}
    return json.loads(USERS_FILE.read_text(encoding="utf-8"))

def save_users(users):
    try:
        with open("data/users.json", "w", encoding="utf-8") as f:
            json.dump(users, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"🛑 КРИТИЧЕСКАЯ ОШИБКА СОХРАНЕНИЯ: {e}")

def generate_uid(users: dict):
    while True:
        uid = "".join(random.choices(ALPHABET, k=8))
        if not any(u.get("uid") == uid for u in users.values()):
            return uid

def get_text(filename: str) -> str:
    path = BASE_DIR / "data" / "texts" / filename
    if not path.exists():
        return f"Текст {filename} не найден"
    return path.read_text(encoding="utf-8")

# Добавьте ADMIN_ID (ваш ID)
ADMIN_TO_RECEIVE = 7419340290

def save_users(users, bot=None):
    try:
        # 1. Сохраняем локально
        with open("data/users.json", "w", encoding="utf-8") as f:
            json.dump(users, f, indent=4, ensure_ascii=False)
        
        # 2. Если передан объект бота, отправляем файл админу
        if bot:
            async def send_backup():
                try:
                    document = FSInputFile("data/users.json")
                    await bot.send_document(
                        ADMIN_TO_RECEIVE, 
                        document, 
                        caption=f"📁 Бэкап базы пользователей\n⏰ Время: {os.path.getmtime('data/users.json')}"
                    )
                except Exception as e:
                    print(f"❌ Ошибка отправки бэкапа: {e}")
            
            # Так как save_users обычно вызывается из асинхронных функций, 
            # мы можем использовать текущий цикл событий
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(send_backup())
                
    except Exception as e:
        print(f"🛑 Ошибка сохранения: {e}")