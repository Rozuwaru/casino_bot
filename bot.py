import asyncio
import logging
import os
import random
from aiogram import Bot, Dispatcher, Router, F, BaseMiddleware
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    TelegramObject,
)
from typing import Callable, Dict, Any, Awaitable
from aiohttp import web
from supabase import create_client, Client

# --- КОНФИГУРАЦИЯ ---
TOKEN = "8752641180:AAET94FACuNdO26CCdFHFyv1vJhSiv3O7F4"
SUPABASE_URL = "https://lnskcqunuaewqcsvcpvr.supabase.co"
# Убедитесь, что здесь указан правильный anon public ключ из настроек Supabase:
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imxuc2tjcXVudWFld3Fjc3ZjcHZyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTMwMzE2MjQsImV4cCI6MjEwODYwNzYyNH0.g0F_E6hIOeholtABi_WsbMzqT4H-49wTH5XYXAk_0Nc"

ADMIN_USERNAME = "p0tat0777"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
router = Router()

def fmt(val: float) -> str:
    """Форматирование чисел с разделителями (например, 1,000,000)"""
    return f"{int(val):,}"

def is_admin(user) -> bool:
    """Проверка прав администратора по Telegram юзернейму"""
    if not user.username:
        return False
    return user.username.lower() == ADMIN_USERNAME.lower()

def get_main_menu_kb(user) -> InlineKeyboardMarkup:
    """Динамическое меню: кнопка админки видна только администратору"""
    buttons = [
        [InlineKeyboardButton(text="🎮 Список игр", callback_data="games_list")]
    ]
    if is_admin(user):
        buttons.append([InlineKeyboardButton(text="🛠 Админ-панель", callback_data="admin_panel_cb")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def find_user_in_db(identifier: str):
    """Поиск пользователя в Supabase по ID или юзернейму"""
    clean_id = identifier.strip().lstrip('@')
    try:
        if clean_id.isdigit():
            res = supabase.table('users').select('*').eq('user_id', int(clean_id)).execute()
            if res.data: return res.data[0]
        res = supabase.table('users').select('*').ilike('username', clean_id).execute()
        if res.data: return res.data[0]
    except Exception as e:
        logging.error(f"Find User Error: {e}")
    return None

# --- MIDDLEWARE ДЛЯ УЧЕТА ПОЛЬЗОВАТЕЛЕЙ И СООБЩЕНИЙ ---
class DatabaseMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = None
        if isinstance(event, Message) and event.from_user:
            user = event.from_user
        elif isinstance(event, CallbackQuery) and event.from_user:
            user = event.from_user

        if user:
            user_id = user.id
            username = user.username or user.full_name
            try:
                res = supabase.table('users').select('*').eq('user_id', user_id).execute()
                if res.data and len(res.data) > 0:
                    current_msgs = res.data[0].get('message_count', 0) or 0
                    supabase.table('users').update({
                        'username': username,
                        'message_count': current_msgs + 1
                    }).eq('user_id', user_id).execute()
                else:
                    supabase.table('users').insert({
                        'user_id': user_id,
                        'username': username,
                        'balance': 1000000.0,
                        'message_count': 1
                    }).execute()
            except Exception as e:
                logging.error(f"Middleware DB Error: {e}")

        return await handler(event, data)

async def get_user_balance(user_id: int) -> float:
    try:
        response = supabase.table('users').select('balance').eq('user_id', user_id).execute()
        if response.data and len(response.data) > 0:
            return float(response.data[0]['balance'])
        return 1000000.0
    except Exception as e:
        logging.error(f"Get Balance Error: {e}")
        return 1000000.0

async def update_user_balance_by_id(user_id: int, amount: float) -> float:
    try:
        res = supabase.table('users').select('balance').eq('user_id', user_id).execute()
        current = float(res.data[0]['balance']) if res.data else 1000000.0
        new_balance = current + amount
        supabase.table('users').update({'balance': new_balance}).eq('user_id', user_id).execute()
        return new_balance
    except Exception as e:
        logging.error(f"Update Balance Error: {e}")
        return 0.0

# --- ГЛАВНОЕ МЕНЮ ---
@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    balance = await get_user_balance(user.id)
    admin_badge = " 👑 [Админ]" if is_admin(user) else ""
    username_display = f"@{user.username}" if user.username else user.full_name
    
    text = (
        f"👤 Игрок: {username_display}{admin_badge}\n"
        f"🪙 Баланс: {fmt(balance)} монет"
    )
    await message.answer(text, reply_markup=get_main_menu_kb(user))

@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery):
    user = callback.from_user
    balance = await get_user_balance(user.id)
    admin_badge = " 👑 [Админ]" if is_admin(user) else ""
    username_display = f"@{user.username}" if user.username else user.full_name
    
    text = (
        f"👤 Игрок: {username_display}{admin_badge}\n"
        f"🪙 Баланс: {fmt(balance)} монет"
    )
    await callback.message.edit_text(text, reply_markup=get_main_menu_kb(user))
    await callback.answer()

@router.callback_query(F.data == "games_list")
async def cb_games_list(callback: CallbackQuery):
    text = (
        "🎮 **Список игр и команды для запуска:**\n\n"
        "🎲 **Кости:** `/dice <ставка> <числа...>`\n"
        "   *(Пример: `/dice 100000 3 5` — мульти-ставки с коэффициентом)*\n\n"
        "🎰 **Слоты:** `/slots <ставка>`\n"
        "   *(777 — x10, 77... — x5, 3 одинаковых — x3, 2 одинаковых — x2)*\n\n"
        "🎡 **Рулетка:** `/roulette <ставка>`\n"
        "   *(Открывает реальное игровое поле с кнопками для ставок на множество чисел)*\n\n"
        "🪙 **Монетка:** `/coin <ставка> <heads / tails>`\n"
        "📈 **Хай-Ло:** `/hilo <ставка> <high / low>`\n"
        "🎯 **Дартс:** `/darts <ставка>`\n"
        "🏀 **Баскетбол:** `/basketball <ставка>`\n"
        "⚽ **Футбол:** `/football <ставка>`\n"
        "🎳 **Боулинг:** `/bowling <ставка>`"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="main_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "admin_panel_cb")
async def cb_admin_panel(callback: CallbackQuery):
    if not is_admin(callback.from_user):
        await callback.answer("❌ Доступ запрещен.", show_alert=True)
        return
    
    text = (
        "🛠 **Админ-панель SpadeKing**\n\n"
        "Управление балансом игроков по юзернейму или ID:\n"
        "• `/addbalance <username / id> <сумма>` — выдать монеты\n"
        "• `/subbalance <username / id> <сумма>` — забрать монеты\n"
        "• `/setbalance <username / id> <сумма>` — установить баланс\n"
        "• `/userinfo <username / id>` — информация об игроке\n"
        "• `/stats` — статистика"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="main_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

# --- ИГРОВЫЕ КОМАНДЫ ---

@router.message(Command("dice"))
async def cmd_dice(message: Message):
    args = message.text.split()
    if len(args) < 3:
        await message.answer("⚠️ Использование: `/dice <ставка> <числа от 1 до 6...>`\nПример: `/dice 100000 3 5`", parse_mode="Markdown")
        return
    try:
        bet = float(args[1])
        numbers = [int(x) for x in args[2:]]
        if any(n < 1 or n > 6 for n in numbers) or len(set(numbers)) != len(numbers):
            await message.answer("⚠️ Неверные числа (от 1 до 6, без повторов).")
            return
    except ValueError:
        await message.answer("⚠️ Ошибка в формате.")
        return

    user_id = message.from_user.id
    balance = await get_user_balance(user_id)
    if balance < bet:
        await message.answer(f"❌ Недостаточно средств! Баланс: {fmt(balance)}")
        return

    await update_user_balance_by_id(user_id, -bet)
    dice_msg = await message.answer_dice(emoji="🎲")
    val = dice_msg.dice.value
    await asyncio.sleep(3)

    if val in numbers:
        mult = round(5.8 / len(numbers), 2)
        win = bet * mult
        await update_user_balance_by_id(user_id, win)
        new_bal = await get_user_balance(user_id)
        await message.answer(f"🎲 Выпало {val}. Выигрыш {fmt(win)} (x{mult}). 💸 (Баланс: {fmt(new_bal)})")
    else:
        new_bal = await get_user_balance(user_id)
        await message.answer(f"🎲 Выпало {val}. Проигрыш {fmt(bet)}. 💸 (Баланс: {fmt(new_bal)})")

@router.message(Command("slots"))
async def cmd_slots(message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("⚠️ Использование: `/slots <ставка>`")
        return
    try:
        bet = float(args[1])
    except ValueError:
        return

    user_id = message.from_user.id
    balance = await get_user_balance(user_id)
    if balance < bet:
        await message.answer("❌ Недостаточно средств!")
        return

    await update_user_balance_by_id(user_id, -bet)
    dice_msg = await message.answer_dice(emoji="🎰")
    val = dice_msg.dice.value # 1 до 64
    await asyncio.sleep(3)

    # Декодируем значение слотов (1-64) в 3 барабана (0-3)
    idx = val - 1
    r1, r2, r3 = idx // 16, (idx // 4) % 4, idx % 4

    # Применяем новые правила множителей
    if r1 == 3 and r2 == 3 and r3 == 3:
        mult = 10
        desc = "🔥 ДЖЕКПОТ (777)!"
    elif r1 == 3 and r2 == 3:
        mult = 5
        desc = "✨ Две семерки (77...)!"
    elif r1 == r2 and r2 == r3:
        mult = 3
        desc = "💎 Тройное совпадение!"
    elif r1 == r2:
        mult = 2
        desc = "⭐ Первые два одинаковые!"
    else:
        mult = 0
        desc = "😢 Проигрыш."

    win = bet * mult
    if win > 0:
        await update_user_balance_by_id(user_id, win)
    
    new_bal = await get_user_balance(user_id)
    await message.answer(f"🎰 {desc} Выигрыш: {fmt(win)} 💸 (Баланс: {fmt(new_bal)})" if win > 0 else f"🎰 {desc} Проигрыш {fmt(bet)} 💸 (Баланс: {fmt(new_bal)})")

# --- РЕАЛЬНАЯ РУЛЕТКА ЧЕРЕЗ КНОПКИ (СТАВКИ НА МНОЖЕСТВО ЧИСЕЛ) ---
@router.message(Command("roulette"))
async def cmd_roulette(message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("⚠️ Использование: `/roulette <ставка>`\nПример: `/roulette 100000`", parse_mode="Markdown")
        return
    try:
        bet = float(args[1])
    except ValueError:
        await message.answer("⚠️ Неверный формат ставки.")
        return

    user_id = message.from_user.id
    balance = await get_user_balance(user_id)
    if balance < bet:
        await message.answer(f"❌ Недостаточно средств! Баланс: {fmt(balance)}")
        return

    # Клавиатура реальной рулетки с возможностью ставить на 12-18 чисел за раз
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔴 Красное (18 ч, x2)", callback_data=f"roul:{bet}:red"),
            InlineKeyboardButton(text="⚫ Черное (18 ч, x2)", callback_data=f"roul:{bet}:black")
        ],
        [
            InlineKeyboardButton(text="1-18 (18 ч, x2)", callback_data=f"roul:{bet}:low"),
            InlineKeyboardButton(text="19-36 (18 ч, x2)", callback_data=f"roul:{bet}:high")
        ],
        [
            InlineKeyboardButton(text="Дюжина 1 [1-12] (x3)", callback_data=f"roul:{bet}:dozen1"),
            InlineKeyboardButton(text="Дюжина 2 [13-24] (x3)", callback_data=f"roul:{bet}:dozen2"),
            InlineKeyboardButton(text="Дюжина 3 [25-36] (x3)", callback_data=f"roul:{bet}:dozen3")
        ],
        [
            InlineKeyboardButton(text="Колонка 1 (x3)", callback_data=f"roul:{bet}:col1"),
            InlineKeyboardButton(text="Колонка 2 (x3)", callback_data=f"roul:{bet}:col2"),
            InlineKeyboardButton(text="Колонка 3 (x3)", callback_data=f"roul:{bet}:col3")
        ],
        [
            InlineKeyboardButton(text="🟢 Зеро [0] (x35)", callback_data=f"roul:{bet}:zero")
        ]
    ])

    await message.answer(
        f"🎡 **Рулетка SpadeKing**\nСтавка: **{fmt(bet)} монет**\n\nВыберите тип ставки на игровом поле:",
        reply_markup=kb,
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("roul:"))
async def cb_roulette_play(callback: CallbackQuery):
    _, bet_str, target = callback.data.split(":")
    bet = float(bet_str)
    user_id = callback.from_user.id

    balance = await get_user_balance(user_id)
    if balance < bet:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return

    await update_user_balance_by_id(user_id, -bet)
    
    # Крутим реальную рулетку (0 - 36)
    num = random.randint(0, 36)
    red_set = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
    color = "zero" if num == 0 else ("red" if num in red_set else "black")

    mult = 0
    if target == "red" and color == "red": mult = 2
    elif target == "black" and color == "black": mult = 2
    elif target == "low" and 1 <= num <= 18: mult = 2
    elif target == "high" and 19 <= num <= 36: mult = 2
    elif target == "dozen1" and 1 <= num <= 12: mult = 3
    elif target == "dozen2" and 13 <= num <= 24: mult = 3
    elif target == "dozen3" and 25 <= num <= 36: mult = 3
    elif target == "col1" and num > 0 and num % 3 == 1: mult = 3
    elif target == "col2" and num > 0 and num % 3 == 2: mult = 3
    elif target == "col3" and num > 0 and num % 3 == 0: mult = 3
    elif target == "zero" and num == 0: mult = 35

    win = bet * mult
    if win > 0:
        await update_user_balance_by_id(user_id, win)
        text = f"🎡 Выпало **{num}** ({color.upper()}). 🎉 Победа! Выигрыш {fmt(win)} монет (x{mult})!"
    else:
        text = f"🎡 Выпало **{num}** ({color.upper()}). 😢 Проигрыш {fmt(bet)} монет."

    new_bal = await get_user_balance(user_id)
    await callback.message.edit_text(f"{text} 💸 (Баланс: {fmt(new_bal)})", parse_mode="Markdown")
    await callback.answer()

@router.message(Command("coin"))
async def cmd_coin(message: Message):
    args = message.text.split()
    if len(args) < 3: return
    bet, target = float(args[1]), args[2].lower()
    user_id = message.from_user.id
    if await get_user_balance(user_id) < bet: return await message.answer("❌ Недостаточно средств!")

    await update_user_balance_by_id(user_id, -bet)
    res_coin = random.choice(["heads", "tails"])
    win = bet * 2 if target == res_coin else 0
    if win > 0: await update_user_balance_by_id(user_id, win)
    new_bal = await get_user_balance(user_id)
    await message.answer(f"🪙 Выпал {'Орел' if res_coin=='heads' else 'Решка'}. {'Победа ' + fmt(win) if win > 0 else 'Проигрыш'} 💸 (Баланс: {fmt(new_bal)})")

@router.message(Command("hilo"))
async def cmd_hilo(message: Message):
    args = message.text.split()
    if len(args) < 3: return
    bet, target = float(args[1]), args[2].lower()
    user_id = message.from_user.id
    if await get_user_balance(user_id) < bet: return await message.answer("❌ Недостаточно средств!")

    await update_user_balance_by_id(user_id, -bet)
    p, n = random.randint(2, 13), random.randint(2, 13)
    win = bet * 1.8 if (target == "high" and n > p) or (target == "low" and n < p) else 0
    if win > 0: await update_user_balance_by_id(user_id, win)
    new_bal = await get_user_balance(user_id)
    await message.answer(f"📈 Карта: {n} (прошлая: {p}). {'Победа ' + fmt(win) if win > 0 else 'Проигрыш'} 💸 (Баланс: {fmt(new_bal)})")

async def process_sport(message: Message, emoji: str, cond):
    args = message.text.split()
    if len(args) < 2: return
    bet = float(args[1])
    user_id = message.from_user.id
    if await get_user_balance(user_id) < bet: return await message.answer("❌ Недостаточно средств!")

    await update_user_balance_by_id(user_id, -bet)
    dice = await message.answer_dice(emoji=emoji)
    val = dice.dice.value
    await asyncio.sleep(3)
    mult = cond(val)
    win = bet * mult
    if win > 0: await update_user_balance_by_id(user_id, win)
    new_bal = await get_user_balance(user_id)
    await message.answer(f"{emoji} Результат: {val}. {'Победа ' + fmt(win) if win > 0 else 'Проигрыш'} 💸 (Баланс: {fmt(new_bal)})")

@router.message(Command("darts"))
async def cmd_darts(message: Message): await process_sport(message, "🎯", lambda v: 5 if v == 6 else (1.5 if v >= 4 else 0))
@router.message(Command("basketball"))
async def cmd_basketball(message: Message): await process_sport(message, "🏀", lambda v: 2 if v >= 4 else 0)
@router.message(Command("football"))
async def cmd_football(message: Message): await process_sport(message, "⚽", lambda v: 1.8 if v >= 3 else 0)
@router.message(Command("bowling"))
async def cmd_bowling(message: Message): await process_sport(message, "🎳", lambda v: 4 if v == 6 else (1.5 if v >= 4 else 0))

# --- АДМИН-ПАНЕЛЬ (УПРАВЛЕНИЕ ПО ЮЗЕРНЕЙМУ ИЛИ ID) ---
@router.message(Command("addbalance", "subbalance", "setbalance", "userinfo"))
async def admin_actions_handler(message: Message):
    if not is_admin(message.from_user):
        return
    
    args = message.text.split()
    cmd = args[0].lstrip('/')
    if len(args) < 2:
        await message.answer(f"⚠️ Использование: `/{cmd} <username или id> [сумма]`", parse_mode="Markdown")
        return
    
    target_arg = args[1]
    target_user = await find_user_in_db(target_arg)
    
    if not target_user:
        await message.answer(f"❌ Пользователь `{target_arg}` не найден в базе данных.", parse_mode="Markdown")
        return
    
    target_id = target_user['user_id']
    target_name = f"@{target_user['username']}" if target_user.get('username') else str(target_id)

    if cmd == "userinfo":
        info = (
            f"👤 **Информация об игроке:**\n"
            f"• ID: `{target_id}`\n"
            f"• Юзернейм: {target_name}\n"
            f"• Баланс: {fmt(target_user.get('balance', 0))} монет\n"
            f"• Отправлено сообщений: {target_user.get('message_count', 0)}"
        )
        await message.answer(info, parse_mode="Markdown")
        return

    if len(args) < 3:
        await message.answer("⚠️ Укажите сумму операции.", parse_mode="Markdown")
        return

    try:
        amount = float(args[2])
    except ValueError:
        await message.answer("⚠️ Неверный формат суммы.")
        return

    if cmd == "addbalance":
        new_bal = await update_user_balance_by_id(target_id, amount)
        await message.answer(f"✅ Баланс игрока {target_name} увеличен на {fmt(amount)}. Новый баланс: {fmt(new_bal)}")
    elif cmd == "subbalance":
        new_bal = await update_user_balance_by_id(target_id, -amount)
        await message.answer(f"✅ Списано {fmt(amount)} у игрока {target_name}. Новый баланс: {fmt(new_bal)}")
    elif cmd == "setbalance":
        supabase.table('users').update({'balance': amount}).eq('user_id', target_id).execute()
        await message.answer(f"✅ Баланс игрока {target_name} установлен ровно на {fmt(amount)}")

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not is_admin(message.from_user): return
    try:
        res = supabase.table('users').select('user_id, message_count').execute()
        if res.data:
            total_users = len(res.data)
            total_messages = sum(u.get('message_count', 0) for u in res.data)
            await message.answer(f"📊 **Статистика казино:**\n• Всего игроков: `{total_users}`\n• Всего сообщений: `{fmt(total_messages)}`", parse_mode="Markdown")
        else:
            await message.answer("📊 База пуста.")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

# --- ЗАПУСК ---
async def handle_ping(request: web.Request) -> web.Response:
    return web.Response(text="Bot is active", status=200)

async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())
    
    dp.include_router(router)

    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)

    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logging.info(f"Бот успешно запущен на порту {port}!")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен.")
