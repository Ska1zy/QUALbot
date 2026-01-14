from aiogram import Router, types, F
from utils import load_users
from handlers.start import read_text

router = Router()

@router.callback_query(F.data == "open_ref")
async def open_referrals(call: types.CallbackQuery):
    user_id = str(call.from_user.id) # Ключ в JSON (Telegram ID)
    users = load_users()
    u = users.get(user_id)
    
    if not u:
        # Если пользователя нет в базе, уведомляем об ошибке
        return await call.answer("❌ Профиль не найден. Попробуйте прописать /start")

    # Получаем актуальный юзернейм бота
    bot_info = await call.bot.get_me()
    bot_username = bot_info.username

    # Подставляем данные в текст. 
    # В user_id передаем u.get("username"), чтобы ссылка была с UID (напр. J6R958ya)
    text = read_text(
        "ref.txt",
        bot_username=bot_username,
        user_id=u.get("username", "error"), 
        ref_count=u.get("ref_count", 0),
        ref_earned=u.get("ref_earned", 0)
    )

    # Клавиатура с кнопкой возврата
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="⬅️ В профиль", callback_data="profile")]
    ])

    try:
        await call.message.edit_text(
            text, 
            reply_markup=kb, 
            parse_mode="Markdown", 
            disable_web_page_preview=True
        )
    except Exception as e:
        # В случае ошибки (например, текст не изменился), просто закрываем уведомление
        await call.answer()