import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
)
from aiohttp import web

# ЗАМЕНИ НА СВОЙ ТОКЕН ОТ BOTFATHER
TOKEN = "ТУТ_ТВОЙ_ТОКЕН_БОТА"

# ЗАМЕНИ НА СВОЙ URL С RENDER (например: https://my-casino-bot.onrender.com/webapp)
WEBAPP_URL = "https://ТВОЕ_ПРИЛОЖЕНИЕ.onrender.com/webapp"

# --- БАЗА ДАННЫХ ---
def init_db():
    conn = sqlite3.connect("casino.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 1000
        )
    """)
    conn.commit()
    conn.close()

def add_user(user_id: int):
    conn = sqlite3.connect("casino.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, 1000)", (user_id,))
    conn.commit()
    conn.close()

# --- ИНТЕРАКТИВНОЕ ОКНО КАЗИНО (MINI APP HTML) ---
WEBAPP_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Casino Mini App</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        body {
            background-color: var(--tg-theme-bg-color, #121212);
            color: var(--tg-theme-text-color, #ffffff);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            text-align: center;
            padding: 20px;
            margin: 0;
        }
        .container {
            max-width: 400px;
            margin: 20px auto;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        h0 { color: #f39c12; font-size: 24px; }
        .balance { font-size: 22px; font-weight: bold; margin: 20px 0; color: #2ecc71; }
        .slots { font-size: 36px; margin: 20px 0; letter-spacing: 10px; }
        button {
            background: #f39c12;
            color: #fff;
            border: none;
            padding: 14px 24px;
            font-size: 16px;
            font-weight: bold;
            border-radius: 12px;
            cursor: pointer;
            width: 100%;
            transition: 0.2s;
        }
        button:active { transform: scale(0.97); background: #d68910; }
        #result { font-size: 18px; margin-top: 15px; min-height: 40px; font-weight: 500; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🎰 Cyber Casino</h2>
        <div class="balance">Баланс: <span id="balanceVal">1000</span> 🪙</div>
        <div class="slots" id="slots">🍒 | 🍋 | 🔔</div>
        <button onclick="spin()">Крутить слот (Ставка: 100)</button>
        <div id="result">Сделай ставку!</div>
    </div>
    <script>
        let tg = window.Telegram.WebApp;
        tg.expand();
        let balance = 1000;

        function spin() {
            if (balance < 100) {
                document.getElementById('result').innerText = 'Недостаточно средств!';
                return;
            }
            balance -= 100;
            const items = ['🍒', '🍋', '🔔', '💎', '7️⃣'];
            const r1 = items[Math.floor(Math.random() * items.length)];
            const r2 = items[Math.floor(Math.random() * items.length)];
            const r3 = items[Math.floor(Math.random() * items.length)];
            
            document.getElementById('slots').innerText = `${r1} | ${r2} | ${r3}`;
            
            if (r1 === r2 && r2 === r3) {
                balance += 600;
                document.getElementById('result').innerText = '🎉 ДЖЕКПОТ! +600 монет';
                tg.HapticFeedback.notificationOccurred('success');
            } else if (r1 === r2 || r2 === r3 || r1 === r3) {
                balance += 150;
                document.getElementById('result').innerText = '✨ Выигрыш! +150 монет';
                tg.HapticFeedback.notificationOccurred('warning');
            } else {
                document.getElementById('result').innerText = '😢 Мимо... Попробуй еще раз!';
                tg.HapticFeedback.notificationOccurred('error');
            }
            document.getElementById('balanceVal').innerText = balance;
        }
    </script>
</body>
</html>
"""

async def handle_webapp(request):
    return web.Response(text=WEBAPP_HTML, content_type="text/html")

# --- РОУТЕР БОТА ---
router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    add_user(message.from_user.id)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎰 Открыть Казино", web_app=WebAppInfo(url=WEBAPP_URL))]
        ]
    )
    await message.answer(
        "Привет! Бот успешно подключен.\n\n"
        "Теперь ты можешь запустить казино в **любом чате** без добавления бота. "
        "Просто напиши в строке ввода любого чата имя бота (например, `@имя_твоего_бота`) и нажми на появившуюся кнопку!",
        reply_markup=keyboard
    )

@router.inline_query()
async def inline_handler(query: InlineQuery):
    add_user(query.from_user.id)
    articles = [
        InlineQueryResultArticle(
            id="casino_app",
            title="🎰 Открыть Казино в чате",
            description="Запустить интерактивную игру по одному клику",
            input_message_content=InputTextMessageContent(
                message_text="🎰 Я запустил казино! Присоединяйся к игре."
            ),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🎲 Играть в казино", web_app=WebAppInfo(url=WEBAPP_URL))]
                ]
            )
        )
    ]
    await query.answer(articles, cache_time=1, is_personal=True)

# --- ЗАПУСК БОТА И СЕРВЕРА ---
async def main():
    init_db()
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    app = web.Application()
    app.router.add_get("/webapp", handle_webapp)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 10000)
    await site.start()

    print("Бот и веб-сервер успешно запущены!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
