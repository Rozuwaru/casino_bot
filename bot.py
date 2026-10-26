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
SUPABASE_KEY = "yJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imxuc2tjcXVudWFld3Fjc3ZjcHZyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTMwMzE2MjQsImV4cCI6MjEwODYwNzYyNH0.g0F_E6hIOeholtABi_WsbMzqT4H-49wTH5XYXAk_0Nc"

# Ваш админский юзернейм (установлен из вашего скриншота)
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

# --- MIDDLEWARE ДЛЯ УЧЕТА ПОЛЬЗОВАТЕЛЕЙ И СООБЩЕНИЙ В SUPABASE ---
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
                    # Обновляем юзернейм и увеличиваем счетчик сообщений на 1
                    supabase.table('users').update({
                        'username': username,
                        'message_count': current_msgs + 1
                    }).eq('user_id', user_id).execute()
                else:
                    # Создаем нового пользователя в базе
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

async def update_user_balance(user_id: int, amount: float) -> float:
    current = await get_user_balance(user_id)
    new_balance = current + amount
    try:
        supabase.table('users').update({'balance': new_balance}).eq('user_id', user_id).execute()
    except Exception as e:
        logging.error(f"Update Balance Error: {e}")
    return new_balance

# --- ГЛАВНОЕ МЕНЮ ---
@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    balance = await get_user_balance(user.id)
    username_display = f"@{user.username}" if user.username else user.full_name
    
    text = (
        f"👤 Игрок: {username_display}\n"
        f"🪙 Баланс: {fmt(balance)} монет"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Список игр", callback_data="games_list")]
    ])
    await message.answer(text, reply_markup=kb)

@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery):
    user = callback.from_user
    balance = await get_user_balance(user.id)
    username_display = f"@{user.username}" if user.username else user.full_name
    
    text = (
        f"👤 Игрок: {username_display}\n"
        f"🪙 Баланс: {fmt(balance)} монет"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Список игр", callback_data="games_list")]
    ])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data == "games_list")
async def cb_games_list(callback: CallbackQuery):
    text = (
        "🎮 **Список игр и команды для запуска:**\n\n"
        "🎲 **Кости:** `/dice <ставка> <числа...>`\n"
        "   *(Пример: `/dice 100000 3 5` — ставки на несколько чисел с коэффициентом!)*\n\n"
        "🎰 **Слоты:** `/slots <ставка>`\n"
        "   *(Пример: `/slots 50000`)*\n\n"
        "🎡 **Рулетка:** `/roulette <ставка> <red / black / zero / 0-36>`\n"
        "   *(Пример: `/roulette 100000 red`)*\n\n"
        "🪙 **Монетка:** `/coin <ставка> <heads / tails>`\n"
        "   *(Пример: `/coin 50000 heads`)*\n\n"
        "📈 **Хай-Ло:** `/hilo <ставка> <high / low>`\n"
        "   *(Пример: `/hilo 50000 high`)*\n\n"
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

# --- ИГРОВЫЕ КОМАНДЫ ---

@router.message(Command("dice"))
async def cmd_dice(message: Message):
    args = message.text.split()
    if len(args) < 3:
        await message.answer("⚠️ Использование: `/dice <ставка> <числа от 1 до 6...>`\nПример: `/dice 100000000 3 5`", parse_mode="Markdown")
        return
    try:
        bet = float(args[1])
        numbers = [int(x) for x in args[2:]]
        if any(n < 1 or n > 6 for n in numbers):
            await message.answer("⚠️ Числа на кубике должны быть от 1 до 6!")
            return
        if len(set(numbers)) != len(numbers):
            await message.answer("⚠️ Числа не должны повторяться!")
            return
    except ValueError:
        await message.answer("⚠️ Неверный формат ставки или чисел!")
        return

    user_id = message.from_user.id
    balance = await get_user_balance(user_id)
    if balance < bet:
        await message.answer(f"❌ Недостаточно средств! Ваш баланс: {fmt(balance)} монет.")
        return

    await update_user_balance(user_id, -bet)
    dice_msg = await message.answer_dice(emoji="🎲")
    val = dice_msg.dice.value
    await asyncio.sleep(3)

    if val in numbers:
        mult = round(5.8 / len(numbers), 2)
        win = bet * mult
        await update_user_balance(user_id, win)
        new_bal = await get_user_balance(user_id)
        await message.answer(f"🎲 Выпало {val}. Выигрыш {fmt(win)} монет (x{mult}). 💸 (Баланс: {fmt(new_bal)})")
    else:
        new_bal = await get_user_balance(user_id)
        await message.answer(f"🎲 Выпало {val}. Проигрыш {fmt(bet)} монет. 💸 (Баланс: {fmt(new_bal)})")

@router.message(Command("slots"))
async def cmd_slots(message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("⚠️ Использование: `/slots <ставка>`", parse_mode="Markdown")
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

    await update_user_balance(user_id, -bet)
    dice_msg = await message.answer_dice(emoji="🎰")
    val = dice_msg.dice.value
    await asyncio.sleep(3)

    win = 0.0
    if val == 64:
        win = bet * 10
        res = f"🎰 ДЖЕКПОТ! Выигрыш {fmt(win)} монет!"
    elif val in [1, 22, 43]:
        win = bet * 2
        res = f"🎰 Совпадение! Выигрыш {fmt(win)} монет!"
    else:
        res = f"🎰 Проигрыш {fmt(bet)} монет."

    if win > 0:
        await update_user_balance(user_id, win)
    
    new_bal = await get_user_balance(user_id)
    await message.answer(f"{res} 💸 (Баланс: {fmt(new_bal)})")

@router.message(Command("roulette"))
async def cmd_roulette(message: Message):
    args = message.text.split()
    if len(args) < 3:
        await message.answer("⚠️ Использование: `/roulette <ставка> <red / black / zero / число 0-36>`", parse_mode="Markdown")
        return
    try:
        bet = float(args[1])
        target = args[2].lower()
    except ValueError:
        return

    user_id = message.from_user.id
    balance = await get_user_balance(user_id)
    if balance < bet:
        await message.answer("❌ Недостаточно средств!")
        return

    await update_user_balance(user_id, -bet)
    num = random.randint(0, 36)
    color = "zero" if num == 0 else ("red" if num % 2 != 0 else "black")

    won = False
    mult = 0
    if target == "red" and color == "red":
        won, mult = True, 2
    elif target == "black" and color == "black":
        won, mult = True, 2
    elif target == "zero" and color == "zero":
        won, mult = True, 14
    elif target.isdigit() and int(target) == num:
        won, mult = True, 35

    if won:
        win = bet * mult
        await update_user_balance(user_id, win)
        text = f"🎡 Выпало {num} ({color}). Победа! Выигрыш {fmt(win)} монет!"
    else:
        text = f"🎡 Выпало {num} ({color}). Проигрыш {fmt(bet)} монет."

    new_bal = await get_user_balance(user_id)
    await message.answer(f"{text} 💸 (Баланс: {fmt(new_bal)})")

@router.message(Command("coin"))
async def cmd_coin(message: Message):
    args = message.text.split()
    if len(args) < 3:
        await message.answer("⚠️ Использование: `/coin <ставка> <heads / tails>`", parse_mode="Markdown")
        return
    try:
        bet = float(args[1])
        target = args[2].lower()
    except ValueError:
        return

    user_id = message.from_user.id
    balance = await get_user_balance(user_id)
    if balance < bet:
        await message.answer("❌ Недостаточно средств!")
        return

    await update_user_balance(user_id, -bet)
    res_coin = random.choice(["heads", "tails"])

    if target == res_coin:
        win = bet * 2
        await update_user_balance(user_id, win)
        text = f"🪙 Выпал {'Орел' if res_coin=='heads' else 'Решка'}. Победа! Выигрыш {fmt(win)} монет!"
    else:
        text = f"🪙 Выпал {'Орел' if res_coin=='heads' else 'Решка'}. Проигрыш {fmt(bet)} монет."

    new_bal = await get_user_balance(user_id)
    await message.answer(f"{text} 💸 (Баланс: {fmt(new_bal)})")

@router.message(Command("hilo"))
async def cmd_hilo(message: Message):
    args = message.text.split()
    if len(args) < 3:
        await message.answer("⚠️ Использование: `/hilo <ставка> <high / low>`", parse_mode="Markdown")
        return
    try:
        bet = float(args[1])
        target = args[2].lower()
    except ValueError:
        return

    user_id = message.from_user.id
    balance = await get_user_balance(user_id)
    if balance < bet:
        await message.answer("❌ Недостаточно средств!")
        return

    await update_user_balance(user_id, -bet)
    prev_card = random.randint(2, 13)
    next_card = random.randint(2, 13)

    won = False
    if target == "high" and next_card > prev_card:
        won = True
    elif target == "low" and next_card < prev_card:
        won = True

    if won:
        win = bet * 1.8
        await update_user_balance(user_id, win)
        text = f"📈 Карта: {next_card} (прошлая: {prev_card}). Победа! Выигрыш {fmt(win)} монет!"
    else:
        text = f"📈 Карта: {next_card} (прошлая: {prev_card}). Проигрыш {fmt(bet)} монет."

    new_bal = await get_user_balance(user_id)
    await message.answer(f"{text} 💸 (Баланс: {fmt(new_bal)})")

async def process_sport_game(message: Message, emoji: str, win_condition):
    args = message.text.split()
    if len(args) < 2:
        await message.answer(f"⚠️ Использование: `{message.text.split()[0]} <ставка>`", parse_mode="Markdown")
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

    await update_user_balance(user_id, -bet)
    dice_msg = await message.answer_dice(emoji=emoji)
    val = dice_msg.dice.value
    await asyncio.sleep(3)

    mult = win_condition(val)
    if mult > 0:
        win = bet * mult
        await update_user_balance(user_id, win)
        res = f"🎉 Успех! Выигрыш {fmt(win)} монет (x{mult})!"
    else:
        res = f"😢 Проигрыш {fmt(bet)} монет."

    new_bal = await get_user_balance(user_id)
    await message.answer(f"{res} 💸 (Баланс: {fmt(new_bal)})")

@router.message(Command("darts"))
async def cmd_darts(message: Message):
    await process_sport_game(message, "🎯", lambda v: 5 if v == 6 else (1.5 if v >= 4 else 0))

@router.message(Command("basketball"))
async def cmd_basketball(message: Message):
    await process_sport_game(message, "🏀", lambda v: 2 if v >= 4 else 0)

@router.message(Command("football"))
async def cmd_football(message: Message):
    await process_sport_game(message, "⚽", lambda v: 1.8 if v >= 3 else 0)

@router.message(Command("bowling"))
async def cmd_bowling(message: Message):
    await process_sport_game(message, "🎳", lambda v: 4 if v == 6 else (1.5 if v >= 4 else 0))

# --- РАСШИРЕННАЯ АДМИН-ПАНЕЛЬ (УПРАВЛЕНИЕ ЧЕРЕЗ ЮЗЕРНЕЙМ) ---
@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user):
        await message.answer("❌ У вас нет доступа к админ-панели.")
        return
    
    text = (
        "🛠 **Админ-панель SpadeKing**\n\n"
        "Доступные команды:\n"
        "• `/addbalance <user_id> <сумма>` — выдать монеты\n"
        "• `/subbalance <user_id> <сумма>` — забрать монеты\n"
        "• `/setbalance <user_id> <сумма>` — установить точный баланс\n"
        "• `/userinfo <user_id>` — узнать информацию об игроке\n"
        "• `/stats` — общая статистика бота"
    )
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("addbalance"))
async def cmd_add_balance(message: Message):
    if not is_admin(message.from_user):
        return
    args = message.text.split()
    if len(args) < 3:
        await message.answer("⚠️ Использование: `/addbalance <user_id> <сумма>`", parse_mode="Markdown")
        return
    try:
        target_id = int(args[1])
        amount = float(args[2])
    except ValueError:
        await message.answer("⚠️ Неверный формат ID или суммы.")
        return

    new_bal = await update_user_balance(target_id, amount)
    await message.answer(f"✅ Баланс пользователя `{target_id}` увеличен на {fmt(amount)}. Новый баланс: {fmt(new_bal)}", parse_mode="Markdown")

@router.message(Command("subbalance"))
async def cmd_sub_balance(message: Message):
    if not is_admin(message.from_user):
        return
    args = message.text.split()
    if len(args) < 3:
        await message.answer("⚠️ Использование: `/subbalance <user_id> <сумма>`", parse_mode="Markdown")
        return
    try:
        target_id = int(args[1])
        amount = float(args[2])
    except ValueError:
        await message.answer("⚠️ Неверный формат ID или суммы.")
        return

    new_bal = await update_user_balance(target_id, -amount)
    await message.answer(f"✅ У пользователя `{target_id}` списано {fmt(amount)}. Новый баланс: {fmt(new_bal)}", parse_mode="Markdown")

@router.message(Command("setbalance"))
async def cmd_set_balance(message: Message):
    if not is_admin(message.from_user):
        return
    args = message.text.split()
    if len(args) < 3:
        await message.answer("⚠️ Использование: `/setbalance <user_id> <сумма>`", parse_mode="Markdown")
        return
    try:
        target_id = int(args[1])
        amount = float(args[2])
    except ValueError:
        await message.answer("⚠️ Неверный формат ID или суммы.")
        return

    try:
        supabase.table('users').update({'balance': amount}).eq('user_id', target_id).execute()
        await message.answer(f"✅ Баланс пользователя `{target_id}` установлен на ровно {fmt(amount)}", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Ошибка базы данных: {e}")

@router.message(Command("userinfo"))
async def cmd_user_info(message: Message):
    if not is_admin(message.from_user):
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("⚠️ Использование: `/userinfo <user_id>`", parse_mode="Markdown")
        return
    try:
        target_id = int(args[1])
    except ValueError:
        await message.answer("⚠️ Неверный формат ID.")
        return

    try:
        res = supabase.table('users').select('*').eq('user_id', target_id).execute()
        if res.data and len(res.data) > 0:
            u = res.data[0]
            info = (
                f"👤 **Информация о пользователе:**\n"
                f"• ID: `{u.get('user_id')}`\n"
                f"• Имя/Юзернейм: @{u.get('username')}\n"
                f"• Баланс: {fmt(u.get('balance', 0))} монет\n"
                f"• Отправлено сообщений: {u.get('message_count', 0)}"
            )
            await message.answer(info, parse_mode="Markdown")
        else:
            await message.answer("❌ Пользователь не найден в базе данных.")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not is_admin(message.from_user):
        return
    try:
        res = supabase.table('users').select('user_id, message_count').execute()
        if res.data:
            total_users = len(res.data)
            total_messages = sum(u.get('message_count', 0) for u in res.data)
            await message.answer(
                f"📊 **Статистика казино:**\n\n"
                f"• Всего зарегистрировано игроков: `{total_users}`\n"
                f"• Всего отправлено сообщений: `{fmt(total_messages)}`",
                parse_mode="Markdown"
            )
        else:
            await message.answer("📊 База данных пуста.")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

# --- ЗАПУСК ---
async def handle_ping(request: web.Request) -> web.Response:
    return web.Response(text="Bot is active", status=200)

async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    
    # Регистрация middleware для автоматического сохранения/обновления игроков и подсчета сообщений
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
