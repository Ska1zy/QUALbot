import requests
import json
import os
from datetime import datetime, timedelta, timezone
from config import REMNAWAVE_API_KEY, REMNAWAVE_BASE_URL

# Путь к настройкам
SETTINGS_PATH = os.path.join(os.path.dirname(__file__), 'settings.json')

def load_settings():
    try:
        with open("api/settings.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Ошибка загрузки settings.json: {e}")
        return {}

HEADERS = {
    "Authorization": f"Bearer {REMNAWAVE_API_KEY}",
    "Content-Type": "application/json",
    "x-remnawave-client-type": "browser"
}

def get_user_info(username: str):
    """Получает актуальные данные пользователя из API"""
    base_url = REMNAWAVE_BASE_URL.rstrip('/')
    try:
        # Пытаемся получить список (можно добавить лимит, если пользователей много)
        response = requests.get(f"{base_url}/users/?rowsPerPage=9999", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            raw_data = response.json()
            # Проверяем разные структуры ответа
            user_list = raw_data.get("response", [])
            if isinstance(user_list, dict):
                user_list = user_list.get("items", []) or user_list.get("users", []) or list(user_list.values())

            for u in user_list:
                if isinstance(u, dict) and u.get('username') == username:
                    return {
                        "uuid": u.get("uuid"),
                        "username": u.get("username"),
                        "expire_at": u.get("expireAt"),
                        "status": u.get("status"),
                        "sub_url": u.get("subscriptionUrl")
                    }
    except Exception as e:
        print(f"Ошибка поиска пользователя {username}: {e}")
    return None

def create_user(username: str, days: int = None):
    """Создает или продлевает пользователя с суммированием времени"""
    settings = load_settings()
    days = days or settings.get("default_subscription_days", 5)
    base_url = REMNAWAVE_BASE_URL.rstrip('/')
    now = datetime.now(timezone.utc)

    payload = {
        "username": username,
        "status": "ACTIVE",
        "trafficLimitBytes": settings.get("traffic_limit_bytes", 0),
        "trafficLimitStrategy": settings.get("traffic_limit_strategy", "NO_RESET"),
        "description": settings.get("description_template", ""),
        "hwidDeviceLimit": settings.get("hwid_limit", 5),
        "activeInternalSquads": settings.get("internal_squad_uuids", []),
        "externalSquadUuid": settings.get("external_squad_uuid", "")
    }

    try:
        # Шаг 1: Попытка создания
        expire_str = (now + timedelta(days=days)).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        response = requests.post(f"{base_url}/users/", headers=HEADERS, json={**payload, "expireAt": expire_str}, timeout=15)

        # Шаг 2: Если пользователь уже есть (409 или 400 с кодом A019)
        is_exists = (response.status_code == 409) or \
                    (response.status_code == 400 and '"errorCode":"A019"' in response.text)

        if is_exists:
            print(f"DEBUG: Пользователь {username} существует (A019). Начинаем продление...")
            user_obj = get_user_info(username)
            
            if user_obj:
                user_uuid = user_obj.get('uuid')
                current_expire_str = user_obj.get('expire_at')
                
                # Суммирование
                if current_expire_str:
                    current_expire_dt = datetime.fromisoformat(current_expire_str.replace("Z", "+00:00"))
                    start_dt = current_expire_dt if current_expire_dt > now else now
                    new_expire_dt = start_dt + timedelta(days=days)
                else:
                    new_expire_dt = now + timedelta(days=days)

                final_expire_str = new_expire_dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")
                print(f"DEBUG: Обновляем {username} до {final_expire_str}")

                payload["uuid"] = user_uuid
                payload["expireAt"] = final_expire_str
                # В новых версиях PATCH идет на /users (без слеша и без UUID в URL, если он в теле)
                response = requests.patch(f"{base_url}/users", headers=HEADERS, json=payload, timeout=10)
            else:
                print(f"DEBUG: Не удалось найти UUID для {username} в списке.")

        # Результат
        if response.status_code in (200, 201):
            data = response.json().get("response", {})
            return {
                "user_id": data.get("id"),
                "uuid": data.get("uuid"),
                "subscription_link": data.get("subscriptionUrl"),
                "expire_at": data.get("expireAt")
            }
        else:
            print(f"ОШИБКА API: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"🚨 Ошибка: {e}")
        return None