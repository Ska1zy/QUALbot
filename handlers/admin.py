from aiogram import Router, types, F
from aiogram.filters import Command
from config import ADMIN_IDS
from utils import load_users, save_users
from api.remnawave import create_user
from aiogram.types import FSInputFile

router = Router()

# Проверка на права администратора
def is_admin(user_id: int):
    return user_id in ADMIN_IDS

@router.message(Command("admin"))
async def admin_menu(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    text = (
        "<b>🛠 Админ-панель</b>\n\n"
        "Команды:\n"
        "• <code>/give_bal [ID] [сумма]</code> — Выдать баланс\n"
        "• <code>/give_sub [username] [дни]</code> — Выдать подписку напрямую\n"
        "• <code>/stats</code> — Общая статистика\n"
        "• <code>/get_db</code> — выгрузка бд"
    )
    await message.answer(text, parse_mode="HTML")

@router.message(Command("give_bal"))
async def cmd_give_balance(message: types.Message):
    if not is_admin(message.from_user.id): return
    
    args = message.text.split()
    if len(args) < 3:
        return await message.answer("Использование: <code>/give_bal [UID] [сумма]</code>", parse_mode="HTML")
    
    target_uid, amount = args[1], int(args[2])
    users = load_users()
    
    # Ищем Telegram ID (ключ), у которого поле username совпадает с введенным UID
    found_tg_id = None
    for tg_id, data in users.items():
        if data.get("username") == target_uid:
            found_tg_id = tg_id
            break
    
    if found_tg_id:
        # Начисляем баланс найденному пользователю
        users[found_tg_id]["balance"] = users[found_tg_id].get("balance", 0) + amount
        save_users(users, bot=message.bot) # Сохраняем и отправляем бэкап
        
        await message.answer(
            f"✅ Баланс пользователя <b>{target_uid}</b> пополнен на <code>{amount}</code> руб.\n"
            f"Новый баланс: <code>{users[found_tg_id]['balance']}</code> руб.", 
            parse_mode="HTML"
        )
        
        # Опционально: уведомляем пользователя о пополнении
        try:
            await message.bot.send_message(
                found_tg_id, 
                f"💰 Администратор пополнил ваш баланс на <b>{amount}₽</b>"
            )
        except: pass
    else:
        await message.answer(f"❌ Пользователь с UID <code>{target_uid}</code> не найден.")


@router.message(Command("give_sub"))
async def cmd_give_sub(message: types.Message):
    if not is_admin(message.from_user.id): return
    
    args = message.text.split()
    if len(args) < 3:
        return await message.answer("Использование: <code>/give_sub [UID] [дни]</code>", parse_mode="HTML")
    
    target_uid, days = args[1], int(args[2])
    users = load_users()
    
    # 1. Ищем пользователя в нашей базе по его UID (username)
    found_tg_id = None
    for tg_id, data in users.items():
        if data.get("username") == target_uid:
            found_tg_id = tg_id
            break
            
    if not found_tg_id:
        return await message.answer(f"❌ Пользователь с UID <b>{target_uid}</b> не найден в базе бота.", parse_mode="HTML")

    # 2. Вызываем функцию API для продления подписки в панели Remnawave
    # Мы используем target_uid напрямую, так как это и есть логин в панели
    res = create_user(target_uid, days=days)
    
    if res:
        # Уведомляем админа об успехе
        await message.answer(
            f"✅ Подписка пользователя <b>{target_uid}</b> успешно продлена на {days} д.\n"
            f"Telegram ID: <code>{found_tg_id}</code>", 
            parse_mode="HTML"
        )
        
        # 3. Уведомляем самого пользователя
        try:
            await message.bot.send_message(
                found_tg_id, 
                f"🚀 <b>Ваша подписка продлена!</b>\n"
                f"Администратор добавил вам <b>{days}</b> дней доступа к VPN.",
                parse_mode="HTML"
            )
        except:
            pass
    else:
        await message.answer("❌ Ошибка при обращении к API Remnawave. Проверьте логи консоли.")


@router.message(Command("stats"))
async def cmd_stats(message: types.Message):
    if not is_admin(message.from_user.id): return
    
    users = load_users()
    total_users = len(users)
    total_balance = sum(u.get("balance", 0) for u in users.values())
    
    await message.answer(
        f"📊 <b>Статистика бота:</b>\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"💰 Общий баланс всех юзеров: {total_balance} руб.",
        parse_mode="HTML"
    )

@router.message(Command("get_db"))
async def send_db(message: types.Message):
    if message.from_user.id in ADMIN_IDS:
        document = FSInputFile("data/users.json")
        await message.answer_document(document, caption="Актуальная база пользователей.")
    else:
        await message.answer("У вас нет прав.")