import asyncio
import logging
import os
import random
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiohttp import web
from supabase import create_client, Client

# Настройки бота и Supabase
TOKEN = "8752641180:AAET94FACuNdO26CCdFHFyv1vJhSiv3O7F4"
SUPABASE_URL = "https://lnskcqunuaewqcsvcpvr.supabase.co"
SUPABASE_KEY = "yJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imxuc2tjcXVudWFld3Fjc3ZjcHZyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTMwMzE2MjQsImV4cCI6MjEwODYwNzYyNH0.g0F_E6hIOeholtABi_WsbMzqT4H-49wTH5XYXAk_0Nc"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

router = Router()

# --- РАБОТА С БАЗОЙ ДАННЫХ ---
async def get_user_balance(user_id: int) -> float:
    try:
        response = supabase.table('users').select('balance').eq('user_id', user_id).execute()
        if response.data and len(response.data) > 0:
            return float(response.data[0]['balance'])
        else:
            supabase.table('users').insert({'user_id': user_id, 'balance': 1000.0}).execute()
            return 1000.0
    except Exception as e:
        logging.error(f"DB Error: {e}")
        return 1000.0

async def update_user_balance(user_id: int, amount: float) -> float:
    current = await get_user_balance(user_id)
    new_balance = current + amount
    try:
        supabase.table('users').update({'balance': new_balance}).eq('user_id', user_id).execute()
    except Exception as e:
        logging.error(f"DB Update Error: {e}")
    return new_balance

# --- КЛАВИАТУРЫ ---
def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 Игровой зал (Казино)", callback_data="games_lobby")],
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile"), InlineKeyboardButton(text="🎁 Бонус (+100 🪙)", callback_data="claim_bonus")]
    ])

def games_lobby_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Слоты 777 (Анимация)", callback_data="game_slots"), InlineKeyboardButton(text="🎲 Кости (Больше/Меньше)", callback_data="game_dice")],
        [InlineKeyboardButton(text="🎯 Дартс", callback_data="game_darts"), InlineKeyboardButton(text="🏀 Баскетбол", callback_data="game_basketball")],
        [InlineKeyboardButton(text="⚽ Футбол", callback_data="game_football"), InlineKeyboardButton(text="🎳 Боулинг", callback_data="game_bowling")],
        [InlineKeyboardButton(text="🎡 Рулетка (Красное/Черное)", callback_data="game_roulette"), InlineKeyboardButton(text="🪙 Монетка", callback_data="game_coin")],
        [InlineKeyboardButton(text="💣 Минное поле", callback_data="game_mines"), InlineKeyboardButton(text="📈 Хай-Ло", callback_data="game_hilo")],
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="main_menu")]
    ])

def back_to_lobby_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ К списку игр", callback_data="games_lobby")]
    ])

# --- ОБРАБОТЧИКИ КОМАНД И МЕНЮ ---
@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    balance = await get_user_balance(user_id)
    await message.answer(
        f"👑 **Добро пожаловать в SpadeKing Casino!**\n\n"
        f"Ваш баланс: 🪙 **{balance:.2f} монет**\n"
        f"Выберите раздел в меню ниже:",
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    balance = await get_user_balance(user_id)
    await callback.message.edit_text(
        f"👑 **Главное меню SpadeKing Casino**\n\n"
        f"Ваш баланс: 🪙 **{balance:.2f} монет**",
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "profile")
async def cb_profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    balance = await get_user_balance(user_id)
    await callback.message.edit_text(
        f"👤 **Профиль игрока**\n\n"
        f"🆔 ID: `{user_id}`\n"
        f"🪙 Баланс: **{balance:.2f} монет**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]]),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "claim_bonus")
async def cb_bonus(callback: CallbackQuery):
    user_id = callback.from_user.id
    new_bal = await update_user_balance(user_id, 100.0)
    await callback.answer("🎁 Вы получили ежедневный бонус +100 монет!", show_alert=True)
    await callback.message.edit_text(
        f"🎁 **Бонус успешно получен!**\n\nВаш новый баланс: 🪙 **{new_bal:.2f} монет**",
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "games_lobby")
async def cb_games_lobby(callback: CallbackQuery):
    user_id = callback.from_user.id
    balance = await get_user_balance(user_id)
    await callback.message.edit_text(
        f"🎲 **Игровой зал**\nБаланс: 🪙 **{balance:.2f} монет**\n\nВыберите игру:",
        reply_markup=games_lobby_kb(),
        parse_mode="Markdown"
    )
    await callback.answer()

# --- ИГРА 1: СЛОТЫ (НАТИВНАЯ АНИМАЦИЯ TELEGRAM 🎰) ---
@router.callback_query(F.data == "game_slots")
async def cb_game_slots(callback: CallbackQuery):
    user_id = callback.from_user.id
    balance = await get_user_balance(user_id)
    bet = 50.0
    if balance < bet:
        await callback.answer("❌ Недостаточно средств! Нужно минимум 50 монет.", show_alert=True)
        return

    await update_user_balance(user_id, -bet)
    await callback.message.delete()
    
    # Отправляем нативную анимацию слотов Telegram
    dice_msg = await callback.message.answer_dice(emoji="🎰")
    value = dice_msg.dice.value  # значение от 1 до 64 в телеграм-слотах
    
    await asyncio.sleep(3) # ждем пока анимация проиграет

    # Логика выигрыша Telegram slots (комбинации: 1=777, 22=BAR, 43=grapes, 64=lemons и т.д., либо упрощенно по значению)
    # 64 - джекпот (все семерки), 1, 22, 43 - мелкие совпадения
    win = 0.0
    if value == 64:
        win = bet * 10
        msg_text = f"🎉 **ДЖЕКПОТ! Семерки! Вы выиграли +{win} монет!**"
    elif value in [1, 22, 43]:
        win = bet * 2
        msg_text = f"✨ **Пара! Вы выиграли +{win} монет!**"
    else:
        msg_text = f"😢 **Мимо! Попробуйте еще раз.**"

    if win > 0:
        await update_user_balance(user_id, win)

    new_bal = await get_user_balance(user_id)
    await callback.message.answer(
        f"{msg_text}\n\nВаш баланс: 🪙 **{new_bal:.2f} монет**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Крутить еще (50 🪙)", callback_data="game_slots")],
            [InlineKeyboardButton(text="⬅️ К списку игр", callback_data="games_lobby")]
        ]),
        parse_mode="Markdown"
    )

# --- ИГРА 2: КОСТИ (НАТИВНАЯ АНИМАЦИЯ 🎲) ---
@router.callback_query(F.data == "game_dice")
async def cb_game_dice(callback: CallbackQuery):
    await callback.message.edit_text(
        "🎲 **Игра в кости**\n\nУгадайте, выпадет число больше 3 или меньше/равно 3?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📉 Меньше или равно 3 (x2)", callback_data="dice_low")],
            [InlineKeyboardButton(text="📈 Больше 3 (x2)", callback_data="dice_high")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="games_lobby")]
        ]),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.in_({"dice_low", "dice_high"}))
async def cb_dice_play(callback: CallbackQuery):
    user_id = callback.from_user.id
    balance = await get_user_balance(user_id)
    bet = 50.0
    if balance < bet:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return

    await update_user_balance(user_id, -bet)
    choice = callback.data
    await callback.message.delete()

    dice_msg = await callback.message.answer_dice(emoji="🎲")
    val = dice_msg.dice.value
    await asyncio.sleep(3)

    is_high = val > 3
    won = (choice == "dice_high" and is_high) or (choice == "dice_low" and not is_high)

    if won:
        win = bet * 2
        await update_user_balance(user_id, win)
        res_text = f"🎉 **Выпало {val}! Победа! +{win} монет!**"
    else:
        res_text = f"😢 **Выпало {val}. Вы проиграли ставку.**"

    new_bal = await get_user_balance(user_id)
    await callback.message.answer(
        f"{res_text}\n\nБаланс: 🪙 **{new_bal:.2f} монет**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎲 Играть еще", callback_data="game_dice")],
            [InlineKeyboardButton(text="⬅️ К списку игр", callback_data="games_lobby")]
        ]),
        parse_mode="Markdown"
    )

# --- ИГРА 3: ДАРТС (🎯) ---
@router.callback_query(F.data == "game_darts")
async def cb_game_darts(callback: CallbackQuery):
    user_id = callback.from_user.id
    balance = await get_user_balance(user_id)
    bet = 50.0
    if balance < bet:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return

    await update_user_balance(user_id, -bet)
    await callback.message.delete()

    dice_msg = await callback.message.answer_dice(emoji="🎯")
    val = dice_msg.dice.value # 1 до 6 (6 - в яблочко)
    await asyncio.sleep(3)

    win = 0.0
    if val == 6:
        win = bet * 5
        res = f"🎯 **Точно в яблочко! Дзынь! +{win} монет!**"
    elif val >= 4:
        win = bet * 1.5
        res = f"🎯 **Хороший бросок! +{win} монет!**"
    else:
        res = f"🎯 **Мимо центра... Проигрыш.**"

    if win > 0:
        await update_user_balance(user_id, win)

    new_bal = await get_user_balance(user_id)
    await callback.message.answer(
        f"{res}\nБаланс: 🪙 **{new_bal:.2f} монет**",
        reply_markup=back_to_lobby_kb(),
        parse_mode="Markdown"
    )

# --- ИГРА 4: БАСКЕТБОЛ (🏀) ---
@router.callback_query(F.data == "game_basketball")
async def cb_game_bball(callback: CallbackQuery):
    user_id = callback.from_user.id
    balance = await get_user_balance(user_id)
    bet = 50.0
    if balance < bet:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return

    await update_user_balance(user_id, -bet)
    await callback.message.delete()

    dice_msg = await callback.message.answer_dice(emoji="🏀")
    val = dice_msg.dice.value # 1-5 (4,5 - гол)
    await asyncio.sleep(3)

    win = 0.0
    if val >= 4:
        win = bet * 2
        await update_user_balance(user_id, win)
        res = f"🏀 **Мяч в кольце! Гол! +{win} монет!**"
    else:
        res = f"🏀 **Не добросил... Проигрыш.**"

    new_bal = await get_user_balance(user_id)
    await callback.message.answer(
        f"{res}\nБаланс: 🪙 **{new_bal:.2f} монет**",
        reply_markup=back_to_lobby_kb(),
        parse_mode="Markdown"
    )

# --- ИГРА 5: ФУТБОЛ (⚽) ---
@router.callback_query(F.data == "game_football")
async def cb_game_football(callback: CallbackQuery):
    user_id = callback.from_user.id
    balance = await get_user_balance(user_id)
    bet = 50.0
    if balance < bet:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return

    await update_user_balance(user_id, -bet)
    await callback.message.delete()

    dice_msg = await callback.message.answer_dice(emoji="⚽")
    val = dice_msg.dice.value # 1-5 (3,4,5 - гол)
    await asyncio.sleep(3)

    win = 0.0
    if val >= 3:
        win = bet * 1.8
        await update_user_balance(user_id, win)
        res = f"⚽ **Гол в девятку! +{win} монет!**"
    else:
        res = f"⚽ **Вратарь поймал мяч. Проигрыш.**"

    new_bal = await get_user_balance(user_id)
    await callback.message.answer(
        f"{res}\nБаланс: 🪙 **{new_bal:.2f} монет**",
        reply_markup=back_to_lobby_kb(),
        parse_mode="Markdown"
    )

# --- ИГРА 6: БОУЛИНГ (🎳) ---
@router.callback_query(F.data == "game_bowling")
async def cb_game_bowling(callback: CallbackQuery):
    user_id = callback.from_user.id
    balance = await get_user_balance(user_id)
    bet = 50.0
    if balance < bet:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return

    await update_user_balance(user_id, -bet)
    await callback.message.delete()

    dice_msg = await callback.message.answer_dice(emoji="🎳")
    val = dice_msg.dice.value # 1 до 6 (6 - страйк)
    await asyncio.sleep(3)

    win = 0.0
    if val == 6:
        win = bet * 4
        res = f"🎳 **СТРАЙК! Все кегли сбиты! +{win} монет!**"
    elif val >= 4:
        win = bet * 1.5
        res = f"🎳 **Хороший бросок! +{win} монет!**"
    else:
        res = f"🎳 **Мимо кеглей... Проигрыш.**"

    if win > 0:
        await update_user_balance(user_id, win)

    new_bal = await get_user_balance(user_id)
    await callback.message.answer(
        f"{res}\nБаланс: 🪙 **{new_bal:.2f} монет**",
        reply_markup=back_to_lobby_kb(),
        parse_mode="Markdown"
    )

# --- ИГРА 7: РУЛЕТКА В ЧАТЕ ---
@router.callback_query(F.data == "game_roulette")
async def cb_game_roulette(callback: CallbackQuery):
    await callback.message.edit_text(
        "🎡 **Европейская рулетка в чате**\n\nВыберите цвет ставки (ставка 50 монет):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔴 Красное (x2)", callback_data="roul_red"), InlineKeyboardButton(text="⚫ Черное (x2)", callback_data="roul_black")],
            [InlineKeyboardButton(text="🟢 Зеро (x14)", callback_data="roul_zero")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="games_lobby")]
        ]),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.in_({"roul_red", "roul_black", "roul_zero"}))
async def cb_roulette_play(callback: CallbackQuery):
    user_id = callback.from_user.id
    balance = await get_user_balance(user_id)
    bet = 50.0
    if balance < bet:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return

    await update_user_balance(user_id, -bet)
    choice = callback.data

    # Рандом рулетки 0-36
    num = random.randint(0, 36)
    color = "zero" if num == 0 else ("red" if num % 2 != 0 else "black")

    won = False
    mult = 0
    if choice == "roul_red" and color == "red":
        won, mult = True, 2
    elif choice == "roul_black" and color == "black":
        won, mult = True, 2
    elif choice == "roul_zero" and color == "zero":
        won, mult = True, 14

    if won:
        win = bet * mult
        await update_user_balance(user_id, win)
        text = f"🎡 Выпало **{num}** ({color.upper()}). 🎉 **Победа! +{win} монет!**"
    else:
        text = f"🎡 Выпало **{num}** ({color.upper()}). 😢 **Проигрыш.**"

    new_bal = await get_user_balance(user_id)
    await callback.message.edit_text(
        f"{text}\n\nБаланс: 🪙 **{new_bal:.2f} монет**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎡 Крутить снова", callback_data="game_roulette")],
            [InlineKeyboardButton(text="⬅️ К играм", callback_data="games_lobby")]
        ]),
        parse_mode="Markdown"
    )

# --- ИГРА 8: МОНЕТКА ---
@router.callback_query(F.data == "game_coin")
async def cb_game_coin(callback: CallbackQuery):
    await callback.message.edit_text(
        "🪙 **Монетка (Орел или Решка)**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🦅 Орел", callback_data="coin_heads"), InlineKeyboardButton(text="🪙 Решка", callback_data="coin_tails")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="games_lobby")]
        ]),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.in_({"coin_heads", "coin_tails"}))
async def cb_coin_play(callback: CallbackQuery):
    user_id = callback.from_user.id
    balance = await get_user_balance(user_id)
    bet = 50.0
    if balance < bet:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return

    await update_user_balance(user_id, -bet)
    choice = callback.data
    res_coin = random.choice(["coin_heads", "coin_tails"])

    if choice == res_coin:
        win = bet * 2
        await update_user_balance(user_id, win)
        text = f"🪙 Выпал **{'Орел' if res_coin=='coin_heads' else 'Решка'}**! 🎉 **Победа +{win} монет!**"
    else:
        text = f"🪙 Выпал **{'Орел' if res_coin=='coin_heads' else 'Решка'}**. 😢 **Проигрыш.**"

    new_bal = await get_user_balance(user_id)
    await callback.message.edit_text(
        f"{text}\n\nБаланс: 🪙 **{new_bal:.2f} монет**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🪙 Еще раз", callback_data="game_coin")],
            [InlineKeyboardButton(text="⬅️ К играм", callback_data="games_lobby")]
        ]),
        parse_mode="Markdown"
    )

# --- ИГРА 9: МИННОЕ ПОЛЕ В ЧАТЕ ---
@router.callback_query(F.data == "game_mines")
async def cb_game_mines(callback: CallbackQuery):
    user_id = callback.from_user.id
    balance = await get_user_balance(user_id)
    bet = 50.0
    if balance < bet:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return

    await update_user_balance(user_id, -bet)
    
    # Создаем сетку 3х3 (9 ячеек, 2 бомбы)
    bombs = random.sample(range(9), 2)
    
    # Сохраняем состояние игры прямо в callback_data (упрощенно: бэкенд может держать в памяти, но сделаем красивую клавиатуру)
    kb = []
    for r in range(3):
        row = []
        for c in range(3):
            idx = r * 3 + c
            row.append(InlineKeyboardButton(text="🎴", callback_data=f"mine_{idx}_{'_'.join(map(str, bombs))}_0"))
        kb.append(row)
    kb.append([InlineKeyboardButton(text="⬅️ Выход", callback_data="games_lobby")])

    await callback.message.edit_text(
        "💣 **Минное поле (Сетка 3x3)**\nИщите кристаллы 💎 и избегайте бомб 💣!\nСтавка: 50 монет.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("mine_"))
async def cb_mine_click(callback: CallbackQuery):
    parts = callback.data.split("_")
    idx = int(parts[1])
    bombs = [int(x) for x in parts[2:-1]]
    opened = int(parts[-1])

    if idx in bombs:
        await callback.message.edit_text(
            "💥 **БУМ! Вы подорвались на бомбе!** Проигрыш.",
            reply_markup=back_to_lobby_kb(),
            parse_mode="Markdown"
        )
    else:
        new_opened = opened + 1
        if new_opened >= 7: # все безопасные открыты
            user_id = callback.from_user.id
            win = 50.0 * 3.0
            await update_user_balance(user_id, win)
            await callback.message.edit_text(
                f"🎉 **Поздравляем! Вы очистили поле и нашли все кристаллы! Выигрыш +{win} монет!**",
                reply_markup=back_to_lobby_kb(),
                parse_mode="Markdown"
            )
        else:
            await callback.answer(f"💎 Кристалл найден! Множитель растет. Открыто: {new_opened}/7")

# --- ИГРА 10: ХАЙ-ЛО ---
@router.callback_query(F.data == "game_hilo")
async def cb_game_hilo(callback: CallbackQuery):
    card = random.randint(2, 14) # от 2 до Туза (14)
    card_names = {11: "Валет", 12: "Дама", 13: "Король", 14: "Туз"}
    c_name = card_names.get(card, str(card))

    await callback.message.edit_text(
        f"📈 **Хай-Ло**\n\nТекущая карта: **{c_name}**\nСледующая карта будет выше или ниже?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📈 Выше", callback_data=f"hilo_high_{card}"), InlineKeyboardButton(text="📉 Ниже", callback_data=f"hilo_low_{card}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="games_lobby")]
        ]),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("hilo_"))
async def cb_hilo_play(callback: CallbackQuery):
    parts = callback.data.split("_")
    action = parts[1]
    prev_card = int(parts[2])

    user_id = callback.from_user.id
    balance = await get_user_balance(user_id)
    bet = 50.0
    if balance < bet:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return

    await update_user_balance(user_id, -bet)
    next_card = random.randint(2, 14)

    card_names = {11: "Валет", 12: "Дама", 13: "Король", 14: "Туз"}
    p_name = card_names.get(prev_card, str(prev_card))
    n_name = card_names.get(next_card, str(next_card))

    won = False
    if action == "high" and next_card > prev_card:
        won = True
    elif action == "low" and next_card < prev_card:
        won = True

    if won:
        win = bet * 1.8
        await update_user_balance(user_id, win)
        res = f"🃏 Открылась карта: **{n_name}** (прошлая: {p_name}). 🎉 **Победа +{win} монет!**"
    else:
        res = f"🃏 Открылась карта: **{n_name}** (прошлая: {p_name}). 😢 **Не угадали.**"

    new_bal = await get_user_balance(user_id)
    await callback.message.edit_text(
        f"{res}\n\nБаланс: 🪙 **{new_bal:.2f} монет**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📈 Сыграть еще", callback_data="game_hilo")],
            [InlineKeyboardButton(text="⬅️ К играм", callback_data="games_lobby")]
        ]),
        parse_mode="Markdown"
    )

# --- ЗАПУСК СЕРВЕРА AIOHTTP И БОТА ---
async def handle_ping(request: web.Request) -> web.Response:
    return web.Response(text="Bot is active", status=200)

async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    # Веб-сервер для поддержания активности на Render
    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)

    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logging.info(f"Чат-бот казино успешно запущен и слушает порт {port}!")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен.")
