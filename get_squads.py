import requests
from config import REMNAWAVE_API_KEY, REMNAWAVE_BASE_URL

HEADERS = {
    "Authorization": f"Bearer {REMNAWAVE_API_KEY}",
    "Content-Type": "application/json",
    "x-remnawave-client-type": "api"
}

def try_endpoint(path):
    url = f"{REMNAWAVE_BASE_URL}{path}"
    print(f"Проверка: {url}")
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            print(f"✅ Успех! Ответ: {r.json()}")
            return True
        else:
            print(f"❌ Ошибка {r.status_code}: {r.text}")
            return False
    except Exception as e:
        print(f"🚨 Ошибка: {e}")
        return False

print("--- ПОИСК ПРАВИЛЬНОГО ЭНДПОИНТА СКВАДОВ ---")

# Пробуем 3 варианта, которые могут существовать в твоей панели
if not try_endpoint("/squads/internal"):
    if not try_endpoint("/squads/all"):
        if not try_endpoint("/internal-squads"):
             print("\nНи один стандартный путь не сработал.")