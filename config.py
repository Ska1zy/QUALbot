import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
REMNAWAVE_API_KEY = os.getenv("REMNAWAVE_API_KEY")
REMNAWAVE_BASE_URL = os.getenv("REMNAWAVE_BASE_URL")

# Список ID администраторов
ADMIN_IDS = [7419340290] 

# --- НАСТРОЙКИ БОНУСОВ ---
REF_BONUS = 20  # Сумма в рублях, которую получает пригласивший