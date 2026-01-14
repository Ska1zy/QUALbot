import os
import random
import string
from datetime import datetime, timezone
from aiogram import Router, types, F
from aiogram.filters import CommandStart
from utils import load_users, save_users
from api.remnawave import create_user, get_user_info
from config import REF_BONUS  # Не забудьте добавить REF_BONUS в config.py

router = Router()

def read_text(filename, **kwargs):
    path = os.path.join("data", "texts", filename)
    if not os.path.exists(path):
        return f"Ошибка: файл {filename} не найден"
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            # Заменяем ключи {key} на значения из kwargs
            for key, value in kwargs.items():
                content = content.replace(f"{{{key}}}", str(value))
            return content
    except Exception as e:
        print(f"❌ Ошибка чтения текста {filename}: {e}")
        return "⚠️ Ошибка загрузки контента."

def calc_time_left(expire_at_str: str):
    if not expire_at_str: return "Не активна"
    try:
        # Обработка ISO даты от API
        expire_date = datetime.fromisoformat(expire_at_str.replace("Z", "+00:00"))
        delta = expire_date - datetime.now(timezone.utc)
        if delta.total_seconds() <= 0: return "⏳ Истекла"
        return f"{delta.days} д. {delta.seconds // 3600} ч."
    except: return "Ошибка даты"

def get_profile_kb():
    buttons = [
        [types.InlineKeyboardButton(text="🛒 Купить подписку", callback_data="open_shop")],
        [types.InlineKeyboardButton(text="👥 Рефералы", callback_data="open_ref"),
         types.InlineKeyboardButton(text="💳 Пополнить", callback_data="deposit")],
        [types.InlineKeyboardButton(text="🔄 Обновить", callback_data="profile")],
        [types.InlineKeyboardButton(text="🆘 Помощь", url="https://t.me/qualVPN?direct")] # Кнопка помощи
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = str(message.from_user.id)
    users = load_users()
    
    args = message.text.split()
    # Получаем UID из ссылки (например, J6R958ya)
    ref_uid = args[1] if len(args) > 1 else None
    referrer_id = None

    # Поиск Telegram ID по значению username (UID)
    if ref_uid:
        for uid, data in users.items():
            if data.get("username") == ref_uid:
                referrer_id = uid
                break

    if user_id not in users:
        vpn_username = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        res = create_user(vpn_username)
        
        users[user_id] = {
            "username": vpn_username,
            "balance": 0,
            "sub_link": res["subscription_link"] if res else None,
            "referrer": referrer_id if referrer_id != user_id else None,
            "ref_count": 0,
            "ref_earned": 0,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Начисление бонуса, если реферер найден по его UID
        if referrer_id and referrer_id in users and referrer_id != user_id:
            users[referrer_id]["ref_count"] = users[referrer_id].get("ref_count", 0) + 1
            users[referrer_id]["balance"] = users[referrer_id].get("balance", 0) + REF_BONUS
            users[referrer_id]["ref_earned"] = users[referrer_id].get("ref_earned", 0) + REF_BONUS
            
            try:
                await message.bot.send_message(
                    referrer_id, 
                    f"🎁 Вам начислен бонус <b>{REF_BONUS}₽</b> за приглашение друга!",
                    parse_mode="HTML"
                )
            except:
                pass
            
        save_users(users, bot=message.bot)
        await message.answer(read_text("hello.txt", REF_BONUS=REF_BONUS), parse_mode="Markdown")

    await send_profile(message, user_id, users)

async def send_profile(event, user_id, users=None):
    if not users: users = load_users()
    u = users.get(user_id)
    if not u: return

    # Получение актуальных данных из Remnawave API
    api_data = get_user_info(u.get("username"))
    expire_at = api_data.get("expire_at") if api_data else None
    link = (api_data.get("sub_url") if api_data else None) or u.get("sub_link")

    time_left = calc_time_left(expire_at)
    
    # Формирование красивого текста профиля
    text = read_text(
        "profile.txt",
        vpn_id=u.get("username", "—"),
        balance=u.get("balance", 0),
        status="✅ Активен" if "д." in time_left else "❌ Не активен",
        expire_date=time_left,
        sub_link=link or "⚠️ Ошибка"
    )

    # Обработка как обычного сообщения, так и нажатия кнопки (callback)
    if isinstance(event, types.Message):
        await event.answer(text, reply_markup=get_profile_kb(), parse_mode="Markdown", disable_web_page_preview=True)
    else:
        try:
            await event.message.edit_text(text, reply_markup=get_profile_kb(), parse_mode="Markdown", disable_web_page_preview=True)
        except: pass
        await event.answer()

@router.callback_query(F.data == "profile")
async def callback_profile(call: types.CallbackQuery):
    await send_profile(call, str(call.from_user.id))