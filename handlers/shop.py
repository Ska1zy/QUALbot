from aiogram import Router, types, F
from utils import load_users, save_users
import api.remnawave as remna
import os

router = Router()

TARIFS = {
    "30": {"price": 100, "days": 30, "label": "1 месяц"},
    "60": {"price": 190, "days": 60, "label": "2 месяца"},
    "90": {"price": 270, "days": 90, "label": "3 месяца"},
}

def get_shop_msg(key, **kwargs):
    path = os.path.join("data", "texts", "shop_messages.txt")
    if not os.path.exists(path): return "Error: text file missing"
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        try:
            # Простой парсер: ищем блок
            parts = content.split(f"{key}:")
            if len(parts) > 1:
                # Берем текст до следующего двойного переноса или заголовка
                raw_text = parts[1].strip()
                # Отрезаем всё, что идет после следующего ключа (если он есть)
                for next_key in ["INSUFFICIENT_FUNDS", "SUCCESS_BUY", "SHOP_WELCOME"]:
                    if next_key != key and next_key in raw_text:
                         raw_text = raw_text.split(f"{next_key}:")[0]
                return raw_text.strip().format(**kwargs)
        except Exception as e:
            return f"Error parsing: {e}"
    return "Text not found"

# Главное меню магазина
@router.callback_query(F.data == "open_shop")
async def show_shop(callback: types.CallbackQuery):
    users = load_users()
    user_balance = users.get(str(callback.from_user.id), {}).get("balance", 0)

    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="1 Месяц - 100₽", callback_data="buy_30")],
        [types.InlineKeyboardButton(text="2 Месяца - 190₽", callback_data="buy_60")],
        [types.InlineKeyboardButton(text="3 Месяца - 270₽", callback_data="buy_90")],
        [types.InlineKeyboardButton(text="🔙 В профиль", callback_data="profile")]
    ])
    
    text = get_shop_msg("SHOP_WELCOME", balance=user_balance)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

# Заглушка для пополнения
@router.callback_query(F.data == "deposit")
async def deposit_handler(callback: types.CallbackQuery):
    await callback.answer("🚧 Пополнение пока работает только через админа.", show_alert=True)

# Покупка
@router.callback_query(F.data.startswith("buy_"))
async def handle_purchase(callback: types.CallbackQuery):
    days_key = callback.data.split("_")[1]
    tarif = TARIFS.get(days_key)
    user_id = str(callback.from_user.id)
    
    users = load_users()
    user_data = users.get(user_id)

    if user_data["balance"] < tarif["price"]:
        return await callback.message.edit_text(
            get_shop_msg("INSUFFICIENT_FUNDS"),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="💳 Пополнить", callback_data="deposit")],
                [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="open_shop")]
            ]),
            parse_mode="Markdown"
        )

    # Покупаем в API
    result = remna.create_user(user_data["username"], days=tarif["days"])
    
    if result:
        user_data["balance"] -= tarif["price"]
        # Обновляем дату создания, чтобы таймер в профиле сбросился (простое решение)
        from datetime import datetime
        user_data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        save_users(users, bot=message.bot)
        
        await callback.message.edit_text(
            get_shop_msg("SUCCESS_BUY", label=tarif["label"]),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="📱 В профиль", callback_data="profile")]
            ]),
            parse_mode="Markdown"
        )
    else:
        await callback.answer("❌ Ошибка API. Деньги не списаны.", show_alert=True)