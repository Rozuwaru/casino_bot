import asyncio
import logging
import os
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

# Обновленный токен бота
TOKEN = "8752641180:AAET94FACuNdO26CCdFHFyv1vJhSiv3O7F4"

# Ссылка на веб-приложение на Render
WEBAPP_URL = "https://casino-bot-y2qo.onrender.com/webapp"

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

# --- ПРЕМИУМ HTML / CSS / JS ИНТЕРФЕЙС (12 ИГР) ---
WEBAPP_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Grand Royale Casino</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #090a0f;
            --card-bg: #131622;
            --card-hover: #1b1f30;
            --accent-gold: #f7b733;
            --accent-gold-glow: rgba(247, 183, 51, 0.3);
            --accent-red: #ff4757;
            --accent-green: #2ed573;
            --text-main: #ffffff;
            --text-dim: #747d8c;
            --border-color: rgba(255, 255, 255, 0.08);
        }

        * {
            box-sizing: border-box;
            user-select: none;
            -webkit-user-select: none;
            -webkit-tap-highlight-color: transparent;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-main);
            font-family: 'Outfit', sans-serif;
            margin: 0;
            padding: 16px;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .header {
            width: 100%;
            max-width: 440px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: var(--card-bg);
            padding: 14px 20px;
            border-radius: 20px;
            border: 1px solid var(--border-color);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
        }

        .logo {
            font-weight: 800;
            font-size: 18px;
            color: var(--accent-gold);
            text-transform: uppercase;
            letter-spacing: 1.2px;
            text-shadow: 0 0 15px var(--accent-gold-glow);
        }

        .balance-box {
            background: rgba(46, 213, 115, 0.1);
            border: 1px solid rgba(46, 213, 115, 0.3);
            padding: 6px 14px;
            border-radius: 14px;
            font-weight: 700;
            color: var(--accent-green);
            font-size: 15px;
            box-shadow: 0 0 15px rgba(46, 213, 115, 0.15);
            transition: transform 0.2s ease;
        }

        .balance-box.pulse {
            transform: scale(1.1);
        }

        .container {
            width: 100%;
            max-width: 440px;
        }

        .back-btn {
            background: var(--card-bg);
            color: var(--text-main);
            border: 1px solid var(--border-color);
            padding: 10px 18px;
            border-radius: 14px;
            font-weight: 600;
            cursor: pointer;
            margin-bottom: 16px;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s ease;
        }

        .back-btn:active { transform: scale(0.95); background: var(--card-hover); }

        .lobby-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            animation: fadeIn 0.4s ease;
        }

        .game-card {
            background: var(--card-bg);
            border-radius: 20px;
            padding: 18px 12px;
            text-align: center;
            border: 1px solid var(--border-color);
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            position: relative;
            overflow: hidden;
        }

        .game-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background: linear-gradient(135deg, rgba(247, 183, 51, 0.1), transparent);
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        .game-card:hover, .game-card:active {
            transform: translateY(-5px);
            border-color: var(--accent-gold);
            box-shadow: 0 10px 30px var(--accent-gold-glow);
        }

        .game-card:hover::before { opacity: 1; }

        .game-icon {
            font-size: 36px;
            margin-bottom: 8px;
            display: block;
            filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));
        }

        .game-title {
            font-size: 15px;
            font-weight: 600;
            margin-bottom: 4px;
        }

        .game-desc {
            font-size: 11px;
            color: var(--text-dim);
        }

        .game-screen {
            display: none;
            background: var(--card-bg);
            border-radius: 24px;
            padding: 24px 20px;
            border: 1px solid var(--border-color);
            box-shadow: 0 15px 40px rgba(0,0,0,0.6);
            text-align: center;
            animation: slideUp 0.35s cubic-bezier(0.16, 1, 0.3, 1);
        }

        .game-screen.active {
            display: block;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: scale(0.95); }
            to { opacity: 1; transform: scale(1); }
        }

        @keyframes slideUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .bet-control {
            margin: 18px 0;
            display: flex;
            gap: 10px;
            justify-content: center;
            align-items: center;
            background: rgba(0,0,0,0.2);
            padding: 8px 12px;
            border-radius: 14px;
            border: 1px solid var(--border-color);
        }

        .bet-control label {
            font-size: 13px;
            color: var(--text-dim);
            font-weight: 600;
        }

        .bet-input {
            width: 90px;
            background: transparent;
            border: none;
            color: var(--accent-gold);
            font-weight: 800;
            font-size: 18px;
            text-align: center;
            outline: none;
        }

        .action-btn {
            background: linear-gradient(135deg, #f7b733, #fc4a1a);
            color: #000;
            border: none;
            width: 100%;
            padding: 16px;
            font-size: 16px;
            font-weight: 800;
            border-radius: 16px;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 6px 20px rgba(247, 183, 51, 0.3);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .action-btn:active { transform: scale(0.97); box-shadow: 0 2px 10px rgba(247, 183, 51, 0.2); }

        .result-box {
            margin-top: 16px;
            font-weight: 700;
            min-height: 28px;
            font-size: 16px;
            transition: all 0.3s ease;
        }

        .flex-btns {
            display: flex;
            gap: 8px;
            margin-bottom: 14px;
        }

        .flex-btns button {
            flex: 1;
            padding: 12px 8px;
            background: var(--card-hover);
            border: 1px solid var(--border-color);
            color: var(--text-main);
            border-radius: 12px;
            font-weight: 600;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .flex-btns button.selected {
            border-color: var(--accent-gold);
            background: rgba(247, 183, 51, 0.15);
            color: var(--accent-gold);
            box-shadow: 0 0 15px var(--accent-gold-glow);
        }

        /* Анимации игр */
        .slots-reels {
            display: flex;
            justify-content: center;
            gap: 10px;
            font-size: 40px;
            background: rgba(0,0,0,0.4);
            padding: 18px;
            border-radius: 18px;
            border: 2px solid var(--accent-gold);
            margin: 16px 0;
            box-shadow: inset 0 4px 15px rgba(0,0,0,0.8);
        }

        .reel {
            width: 65px; height: 65px;
            line-height: 65px;
            background: rgba(255,255,255,0.04);
            border-radius: 12px;
            transition: transform 0.1s ease;
        }

        .wheel-container {
            position: relative;
            width: 180px; height: 180px;
            margin: 15px auto;
            border-radius: 50%;
            background: conic-gradient(#ff4757 0deg 90deg, #2ed573 90deg 180deg, #f7b733 180deg 270deg, #3742fa 270deg 360deg);
            border: 4px solid var(--accent-gold);
            box-shadow: 0 0 25px var(--accent-gold-glow);
            transition: transform 3s cubic-bezier(0.15, 0.9, 0.2, 1);
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .wheel-pointer {
            position: absolute; top: -12px;
            width: 0; height: 0;
            border-left: 10px solid transparent;
            border-right: 10px solid transparent;
            border-bottom: 20px solid #fff;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.5));
        }

        .plinko-board {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 8px;
            margin: 16px 0;
            background: rgba(0,0,0,0.3);
            padding: 12px;
            border-radius: 16px;
        }
        .plinko-slot {
            background: rgba(255,255,255,0.06);
            padding: 10px;
            border-radius: 10px;
            font-size: 12px;
            font-weight: 700;
            color: var(--accent-gold);
            border: 1px solid var(--border-color);
        }

        .scratch-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin: 16px 0;
        }
        .scratch-card-item {
            background: rgba(255,255,255,0.05);
            border: 1px dashed var(--border-color);
            border-radius: 14px;
            height: 65px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 26px;
            cursor: pointer;
            transition: 0.2s;
        }
        .scratch-card-item.revealed {
            background: rgba(46, 213, 115, 0.15);
            border: 1px solid var(--accent-green);
        }
    </style>
</head>
<body>

    <div class="header">
        <div class="logo">🎰 Casino Royale</div>
        <div class="balance-box" id="balanceBox">🪙 <span id="userBalance">1000</span></div>
    </div>

    <div class="container">

        <!-- ЛОББИ (12 ИГР) -->
        <div id="lobby" class="lobby-grid">
            <div class="game-card" onclick="openGame('slots')"><span class="game-icon">🎰</span><div class="game-title">Слоты 777</div><div class="game-desc">Классика жанра</div></div>
            <div class="game-card" onclick="openGame('roulette')"><span class="game-icon">🎡</span><div class="game-title">Рулетка</div><div class="game-desc">Цвета и зеро</div></div>
            <div class="game-card" onclick="openGame('blackjack')"><span class="game-icon">🃏</span><div class="game-title">Блэкджек</div><div class="game-desc">Собери 21 очко</div></div>
            <div class="game-card" onclick="openGame('mines')"><span class="game-icon">💣</span><div class="game-title">Минное поле</div><div class="game-desc">Ищи кристаллы</div></div>
            <div class="game-card" onclick="openGame('crash')"><span class="game-icon">🚀</span><div class="game-title">Краш X</div><div class="game-desc">Улети до взрыва</div></div>
            <div class="game-card" onclick="openGame('dice')"><span class="game-icon">🎲</span><div class="game-title">Кости</div><div class="game-desc">Больше / Меньше</div></div>
            <div class="game-card" onclick="openGame('coin')"><span class="game-icon">🪙</span><div class="game-title">Монетка</div><div class="game-desc">Орел или Решка</div></div>
            
            <!-- 5 НОВЫХ ИГР -->
            <div class="game-card" onclick="openGame('plinko')"><span class="game-icon">🔺</span><div class="game-title">Плинко</div><div class="game-desc">Пирамида удачи</div></div>
            <div class="game-card" onclick="openGame('hilo')"><span class="game-icon">📈</span><div class="game-title">Хай-Ло</div><div class="game-desc">Выше или ниже</div></div>
            <div class="game-card" onclick="openGame('wheel')"><span class="game-icon">🎯</span><div class="game-title">Колесо Фортуны</div><div class="game-desc">Множители x5</div></div>
            <div class="game-card" onclick="openGame('keno')"><span class="game-icon">🔢</span><div class="game-title">Кено</div><div class="game-desc">Лотерейный тираж</div></div>
            <div class="game-card" onclick="openGame('scratch')"><span class="game-icon">🎫</span><div class="game-title">Скретч-карты</div><div class="game-desc">Стрирай и выигрывай</div></div>
        </div>

        <!-- 1. СЛОТЫ -->
        <div id="game-slots" class="game-screen">
            <button class="back-btn" onclick="showLobby()">⬅ Назад</button>
            <h3>🎰 Слоты 777</h3>
            <div class="slots-reels">
                <div class="reel" id="r1">🍒</div><div class="reel" id="r2">🍋</div><div class="reel" id="r3">🔔</div>
            </div>
            <div class="bet-control"><label>Ставка:</label><input type="number" id="slotsBet" class="bet-input" value="100" min="10"></div>
            <button class="action-btn" onclick="playSlots()">Крутить!</button>
            <div class="result-box" id="slotsResult"></div>
        </div>

        <!-- 2. РУЛЕТКА -->
        <div id="game-roulette" class="game-screen">
            <button class="back-btn" onclick="showLobby()">⬅ Назад</button>
            <h3>🎡 Рулетка</h3>
            <div class="flex-btns">
                <button id="roul-red" onclick="selectRoulette('red')" class="selected">🔴 Красное (x2)</button>
                <button id="roul-black" onclick="selectRoulette('black')">⚫ Черное (x2)</button>
                <button id="roul-zero" onclick="selectRoulette('zero')">🟢 Зеро (x14)</button>
            </div>
            <div class="bet-control"><label>Ставка:</label><input type="number" id="rouletteBet" class="bet-input" value="100" min="10"></div>
            <button class="action-btn" onclick="playRoulette()">Вращать</button>
            <div class="result-box" id="rouletteResult"></div>
        </div>

        <!-- 3. БЛЭКДЖЕК -->
        <div id="game-blackjack" class="game-screen">
            <button class="back-btn" onclick="showLobby()">⬅ Назад</button>
            <h3>🃏 Блэкджек 21</h3>
            <div style="background:rgba(0,0,0,0.2); padding:12px; border-radius:14px; margin:14px 0;">
                <div>Дилер: <span id="bjDealerScore">0</span></div>
                <div style="font-size:22px; margin:6px 0;" id="bjDealerCards">🂠 🂠</div>
                <hr style="border-color:var(--border-color); margin:8px 0;">
                <div>Вы: <span id="bjPlayerScore">0</span></div>
                <div style="font-size:22px; margin:6px 0;" id="bjPlayerCards">❓ ❓</div>
            </div>
            <div class="bet-control"><label>Ставка:</label><input type="number" id="bjBet" class="bet-input" value="100" min="10"></div>
            <div class="flex-btns" id="bjControls" style="display:none;">
                <button onclick="bjHit()" style="background:#2ed573; color:#000;">Взять</button>
                <button onclick="bjStand()" style="background:#ff4757; color:#fff;">Хватит</button>
            </div>
            <button class="action-btn" id="bjStartBtn" onclick="startBlackjack()">Раздать карты</button>
            <div class="result-box" id="bjResult"></div>
        </div>

        <!-- 4. МИННОЕ ПОЛЕ -->
        <div id="game-mines" class="game-screen">
            <button class="back-btn" onclick="showLobby()">⬅ Назад</button>
            <h3>💣 Минное поле</h3>
            <div id="minesGrid" style="display:grid; grid-template-columns:repeat(5, 1fr); gap:6px; margin:16px 0;"></div>
            <div class="bet-control"><label>Ставка:</label><input type="number" id="minesBet" class="bet-input" value="100" min="10"></div>
            <button class="action-btn" id="minesStartBtn" onclick="startMines()">Начать</button>
            <button class="action-btn" id="minesCashoutBtn" onclick="cashoutMines()" style="display:none; background:#2ed573; margin-top:8px;">Забрать</button>
            <div class="result-box" id="minesResult"></div>
        </div>

        <!-- 5. КРАШ -->
        <div id="game-crash" class="game-screen">
            <button class="back-btn" onclick="showLobby()">⬅ Назад</button>
            <h3>🚀 Краш X</h3>
            <div style="background:#000; height:120px; border-radius:14px; display:flex; align-items:center; justify-content:center; font-size:38px; font-weight:800; color:var(--accent-gold); margin:16px 0; border:1px solid var(--border-color);" id="crashDisplay">1.00x</div>
            <div class="bet-control"><label>Ставка:</label><input type="number" id="crashBet" class="bet-input" value="100" min="10"></div>
            <button class="action-btn" id="crashBtn" onclick="startCrash()">Старт</button>
            <div class="result-box" id="crashResult"></div>
        </div>

        <!-- 6. КОСТИ -->
        <div id="game-dice" class="game-screen">
            <button class="back-btn" onclick="showLobby()">⬅ Назад</button>
            <h3>🎲 Кости</h3>
            <div class="flex-btns">
                <button id="dice-low" onclick="selectDice('low')" class="selected">Меньше 4 (x2)</button>
                <button id="dice-high" onclick="selectDice('high')">Больше 3 (x2)</button>
            </div>
            <div class="bet-control"><label>Ставка:</label><input type="number" id="diceBet" class="bet-input" value="100" min="10"></div>
            <button class="action-btn" onclick="playDice()">Бросить</button>
            <div class="result-box" id="diceResult"></div>
        </div>

        <!-- 7. МОНЕТКА -->
        <div id="game-coin" class="game-screen">
            <button class="back-btn" onclick="showLobby()">⬅ Назад</button>
            <h3>🪙 Монетка</h3>
            <div class="flex-btns">
                <button id="coin-heads" onclick="selectCoin('heads')" class="selected">🦅 Орел</button>
                <button id="coin-tails" onclick="selectCoin('tails')">🪙 Решка</button>
            </div>
            <div class="bet-control"><label>Ставка:</label><input type="number" id="coinBet" class="bet-input" value="100" min="10"></div>
            <button class="action-btn" onclick="playCoin()">Подкинуть</button>
            <div class="result-box" id="coinResult"></div>
        </div>

        <!-- 8. ПЛИНКО (НОВАЯ) -->
        <div id="game-plinko" class="game-screen">
            <button class="back-btn" onclick="showLobby()">⬅ Назад</button>
            <h3>🔺 Плинко</h3>
            <div class="plinko-board">
                <div class="plinko-slot">0.2x</div>
                <div class="plinko-slot">0.5x</div>
                <div class="plinko-slot">2x</div>
                <div class="plinko-slot">5x</div>
                <div class="plinko-slot">10x</div>
            </div>
            <div class="bet-control"><label>Ставка:</label><input type="number" id="plinkoBet" class="bet-input" value="100" min="10"></div>
            <button class="action-btn" onclick="playPlinko()">Запустить шар</button>
            <div class="result-box" id="plinkoResult"></div>
        </div>

        <!-- 9. ХАЙ-ЛО (НОВАЯ) -->
        <div id="game-hilo" class="game-screen">
            <button class="back-btn" onclick="showLobby()">⬅ Назад</button>
            <h3>📈 Хай-Ло</h3>
            <div style="font-size:48px; margin:20px 0;" id="hiloCard">🂡</div>
            <div class="flex-btns">
                <button onclick="playHilo('lower')">📉 Ниже</button>
                <button onclick="playHilo('higher')">📈 Выше</button>
            </div>
            <div class="bet-control"><label>Ставка:</label><input type="number" id="hiloBet" class="bet-input" value="100" min="10"></div>
            <div class="result-box" id="hiloResult">Сделайте ставку и угадайте карту</div>
        </div>

        <!-- 10. КОЛЕСО ФОРТУНЫ (НОВАЯ) -->
        <div id="game-wheel" class="game-screen">
            <button class="back-btn" onclick="showLobby()">⬅ Назад</button>
            <h3>🎯 Колесо Фортуны</h3>
            <div style="position:relative; width:140px; height:140px; margin:20px auto;">
                <div class="wheel-pointer"></div>
                <div class="wheel-container" id="fortuneWheel"></div>
            </div>
            <div class="bet-control"><label>Ставка:</label><input type="number" id="wheelBet" class="bet-input" value="100" min="10"></div>
            <button class="action-btn" onclick="playWheel()">Крутить колесо</button>
            <div class="result-box" id="wheelResult"></div>
        </div>

        <!-- 11. КЕНО (НОВАЯ) -->
        <div id="game-keno" class="game-screen">
            <button class="back-btn" onclick="showLobby()">⬅ Назад</button>
            <h3>🔢 Кено Лото</h3>
            <div style="font-size:13px; color:var(--text-dim); margin-bottom:10px;">Выпало чисел: <span id="kenoDrawn" style="color:var(--accent-gold); font-weight:bold;">-</span></div>
            <div class="bet-control"><label>Ставка:</label><input type="number" id="kenoBet" class="bet-input" value="100" min="10"></div>
            <button class="action-btn" onclick="playKeno()">Розыгрыш тиража</button>
            <div class="result-box" id="kenoResult"></div>
        </div>

        <!-- 12. СКРЕТЧ-КАРТЫ (НОВАЯ) -->
        <div id="game-scratch" class="game-screen">
            <button class="back-btn" onclick="showLobby()">⬅ Назад</button>
            <h3>🎫 Скретч-карты</h3>
            <div class="scratch-grid" id="scratchGrid">
                <div class="scratch-card-item" onclick="revealScratch(0)" id="sc0">❓</div>
                <div class="scratch-card-item" onclick="revealScratch(1)" id="sc1">❓</div>
                <div class="scratch-card-item" onclick="revealScratch(2)" id="sc2">❓</div>
                <div class="scratch-card-item" onclick="revealScratch(3)" id="sc3">❓</div>
            </div>
            <div class="bet-control"><label>Ставка:</label><input type="number" id="scratchBet" class="bet-input" value="100" min="10"></div>
            <button class="action-btn" onclick="startScratch()">Новая карта</button>
            <div class="result-box" id="scratchResult">Сотрите ячейки</div>
        </div>

    </div>

    <script>
        let tg = window.Telegram.WebApp;
        tg.expand();

        let balance = 1000;
        function updateBalance(amount) {
            balance += amount;
            let el = document.getElementById('userBalance');
            let box = document.getElementById('balanceBox');
            el.innerText = balance;
            box.classList.add('pulse');
            setTimeout(() => box.classList.remove('pulse'), 200);
        }

        function triggerHaptic(type = 'medium') {
            if (tg.HapticFeedback) {
                if (type === 'success') tg.HapticFeedback.notificationOccurred('success');
                else if (type === 'error') tg.HapticFeedback.notificationOccurred('error');
                else tg.HapticFeedback.impactOccurred(type);
            }
        }

        function showLobby() {
            document.querySelectorAll('.game-screen').forEach(el => el.classList.remove('active'));
            document.getElementById('lobby').style.display = 'grid';
        }

        function openGame(gameId) {
            triggerHaptic('light');
            document.getElementById('lobby').style.display = 'none';
            document.getElementById(`game-${gameId}`).classList.add('active');
        }

        /* --- СЛОТЫ --- */
        function playSlots() {
            let bet = parseInt(document.getElementById('slotsBet').value);
            if (bet > balance || bet <= 0) return alert('Недостаточно средств!');
            updateBalance(-bet);
            triggerHaptic('heavy');

            let items = ['🍒', '🍋', '🔔', '💎', '7️⃣'];
            let r1 = document.getElementById('r1'), r2 = document.getElementById('r2'), r3 = document.getElementById('r3');
            let timer = setInterval(() => {
                r1.innerText = items[Math.floor(Math.random() * items.length)];
                r2.innerText = items[Math.floor(Math.random() * items.length)];
                r3.innerText = items[Math.floor(Math.random() * items.length)];
            }, 70);

            setTimeout(() => {
                clearInterval(timer);
                let res1 = items[Math.floor(Math.random() * items.length)];
                let res2 = items[Math.floor(Math.random() * items.length)];
                let res3 = items[Math.floor(Math.random() * items.length)];
                r1.innerText = res1; r2.innerText = res2; r3.innerText = res3;

                let resBox = document.getElementById('slotsResult');
                if (res1 === res2 && res2 === res3) {
                    let win = bet * 5; updateBalance(win);
                    resBox.innerHTML = `<span style="color:var(--accent-gold);">🎉 ДЖЕКПОТ! +${win}</span>`;
                    triggerHaptic('success');
                } else if (res1 === res2 || res2 === res3 || res1 === res3) {
                    let win = Math.floor(bet * 1.5); updateBalance(win);
                    resBox.innerHTML = `<span style="color:var(--accent-green);">✨ Пара! +${win}</span>`;
                    triggerHaptic('success');
                } else {
                    resBox.innerHTML = `<span style="color:var(--accent-red);">😢 Мимо...</span>`;
                    triggerHaptic('error');
                }
            }, 900);
        }

        /* --- РУЛЕТКА --- */
        let selectedRoulette = 'red';
        function selectRoulette(val) {
            selectedRoulette = val;
            document.querySelectorAll('#game-roulette .flex-btns button').forEach(b => b.classList.remove('selected'));
            document.getElementById(`roul-${val}`).classList.add('selected');
        }
        function playRoulette() {
            let bet = parseInt(document.getElementById('rouletteBet').value);
            if (bet > balance || bet <= 0) return alert('Недостаточно средств!');
            updateBalance(-bet);
            triggerHaptic('heavy');
            let num = Math.floor(Math.random() * 37);
            let color = num === 0 ? 'zero' : (num % 2 === 0 ? 'black' : 'red');
            let resBox = document.getElementById('rouletteResult');
            if (color === selectedRoulette) {
                let mult = selectedRoulette === 'zero' ? 14 : 2;
                let win = bet * mult; updateBalance(win);
                resBox.innerHTML = `<span style="color:var(--accent-green);">🎯 Выпало ${num} (${color.toUpperCase()})! +${win}</span>`;
                triggerHaptic('success');
            } else {
                resBox.innerHTML = `<span style="color:var(--accent-red);">❌ Выпало ${num} (${color.toUpperCase()}). Проигрыш</span>`;
                triggerHaptic('error');
            }
        }

        /* --- БЛЭКДЖЕК --- */
        let bjState = { player: [], dealer: [], playing: false };
        function getCard() { return Math.min(10, Math.floor(Math.random() * 10) + 1); }
        function sumHand(h) { return h.reduce((a,b)=>a+b, 0); }
        function startBlackjack() {
            let bet = parseInt(document.getElementById('bjBet').value);
            if (bet > balance || bet <= 0) return alert('Недостаточно средств!');
            updateBalance(-bet); triggerHaptic('medium');
            bjState = { player: [getCard(), getCard()], dealer: [getCard()], playing: true };
            document.getElementById('bjStartBtn').style.display = 'none';
            document.getElementById('bjControls').style.display = 'flex';
            document.getElementById('bjResult').innerText = '';
            renderBJ();
        }
        function renderBJ() {
            document.getElementById('bjPlayerCards').innerText = bjState.player.join(' ');
            document.getElementById('bjDealerCards').innerText = bjState.dealer.join(' ') + ' 🂠';
            document.getElementById('bjPlayerScore').innerText = sumHand(bjState.player);
            document.getElementById('bjDealerScore').innerText = sumHand(bjState.dealer);
        }
        function bjHit() {
            if (!bjState.playing) return;
            bjState.player.push(getCard()); renderBJ();
            if (sumHand(bjState.player) > 21) endBJ(false, '💥 Перебор!');
        }
        function bjStand() {
            if (!bjState.playing) return;
            while(sumHand(bjState.dealer) < 17) bjState.dealer.push(getCard());
            let p = sumHand(bjState.player), d = sumHand(bjState.dealer);
            if (d > 21 || p > d) endBJ(true, '🎉 Победа!');
            else if (p === d) endBJ('draw', '🤝 Ничья!');
            else endBJ(false, '😢 Дилер выиграл!');
        }
        function endBJ(win, msg) {
            bjState.playing = false;
            let bet = parseInt(document.getElementById('bjBet').value);
            if (win === true) { updateBalance(bet * 2); triggerHaptic('success'); }
            else if (win === 'draw') { updateBalance(bet); }
            else { triggerHaptic('error'); }
            document.getElementById('bjDealerCards').innerText = bjState.dealer.join(' ');
            document.getElementById('bjDealerScore').innerText = sumHand(bjState.dealer);
            document.getElementById('bjResult').innerText = msg;
            document.getElementById('bjStartBtn').style.display = 'block';
            document.getElementById('bjControls').style.display = 'none';
        }

        /* --- МИНЫ --- */
        let minesState = { active: false, bombs: [], opened: 0, mult: 1.2 };
        function startMines() {
            let bet = parseInt(document.getElementById('minesBet').value);
            if (bet > balance || bet <= 0) return alert('Недостаточно средств!');
            updateBalance(-bet); triggerHaptic('medium');
            let grid = document.getElementById('minesGrid'); grid.innerHTML = '';
            let bombs = [];
            while(bombs.length < 3) { let r = Math.floor(Math.random()*25); if(!bombs.includes(r)) bombs.push(r); }
            minesState = { active: true, bombs: bombs, opened: 0, mult: 1.2, bet: bet };
            for(let i=0; i<25; i++) {
                let tile = document.createElement('div');
                tile.style.cssText = "aspect-ratio:1; background:rgba(255,255,255,0.06); border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:16px; cursor:pointer;";
                tile.onclick = () => clickMine(i, tile);
                grid.appendChild(tile);
            }
            document.getElementById('minesStartBtn').style.display = 'none';
            document.getElementById('minesCashoutBtn').style.display = 'block';
            document.getElementById('minesResult').innerText = '💎 Ищите кристаллы!';
        }
        function clickMine(idx, tile) {
            if(!minesState.active || tile.style.background.includes('rgb')) return;
            if(minesState.bombs.includes(idx)) {
                tile.style.background = 'rgba(255,71,87,0.3)'; tile.innerText = '💣';
                minesState.active = false;
                document.getElementById('minesResult').innerHTML = '<span style="color:var(--accent-red);">💥 БУМ! Проигрыш</span>';
                document.getElementById('minesStartBtn').style.display = 'block';
                document.getElementById('minesCashoutBtn').style.display = 'none';
                triggerHaptic('error');
            } else {
                tile.style.background = 'rgba(46,213,115,0.3)'; tile.innerText = '💎';
                minesState.opened++; minesState.mult += 0.3;
                let cur = Math.floor(minesState.bet * minesState.mult);
                document.getElementById('minesResult').innerText = `💰 Профит: +${cur} (x${minesState.mult.toFixed(2)})`;
                triggerHaptic('light');
            }
        }
        function cashoutMines() {
            if(!minesState.active || minesState.opened === 0) return;
            let win = Math.floor(minesState.bet * minesState.mult);
            updateBalance(win); minesState.active = false;
            document.getElementById('minesResult').innerHTML = `<span style="color:var(--accent-green);">💰 Забрал +${win}!</span>`;
            document.getElementById('minesStartBtn').style.display = 'block';
            document.getElementById('minesCashoutBtn').style.display = 'none';
            triggerHaptic('success');
        }

        /* --- КРАШ --- */
        let crashInterval = null;
        function startCrash() {
            let bet = parseInt(document.getElementById('crashBet').value);
            if (bet > balance || bet <= 0) return alert('Недостаточно средств!');
            updateBalance(-bet); triggerHaptic('medium');
            let mult = 1.00, crashPoint = (Math.random() * 4 + 1).toFixed(2);
            let btn = document.getElementById('crashBtn'), display = document.getElementById('crashDisplay'), active = true;
            btn.innerText = 'Забрать';
            btn.onclick = () => {
                if(!active) return;
                active = false; clearInterval(crashInterval);
                let win = Math.floor(bet * mult); updateBalance(win);
                document.getElementById('crashResult').innerHTML = `<span style="color:var(--accent-green);">🎉 Успел! +${win}</span>`;
                btn.innerText = 'Старт'; btn.onclick = startCrash; triggerHaptic('success');
            };
            crashInterval = setInterval(() => {
                mult += 0.05; display.innerText = mult.toFixed(2) + 'x';
                if(mult >= crashPoint && active) {
                    active = false; clearInterval(crashInterval);
                    display.innerText = '💥 CRASH!';
                    document.getElementById('crashResult').innerHTML = `<span style="color:var(--accent-red);">😢 Улетел на ${crashPoint}x</span>`;
                    btn.innerText = 'Старт'; btn.onclick = startCrash; triggerHaptic('error');
                }
            }, 100);
        }

        /* --- КОСТИ --- */
        let selectedDice = 'low';
        function selectDice(val) {
            selectedDice = val;
            document.querySelectorAll('#game-dice .flex-btns button').forEach(b => b.classList.remove('selected'));
            document.getElementById(`dice-${val}`).classList.add('selected');
        }
        function playDice() {
            let bet = parseInt(document.getElementById('diceBet').value);
            if (bet > balance || bet <= 0) return alert('Недостаточно средств!');
            updateBalance(-bet); triggerHaptic('medium');
            let roll = Math.floor(Math.random()*6)+1;
            let win = (selectedDice === 'low' && roll <= 3) || (selectedDice === 'high' && roll >= 4);
            let res = document.getElementById('diceResult');
            if(win) {
                updateBalance(bet * 2);
                res.innerHTML = `<span style="color:var(--accent-green);">🎲 Выпало ${roll}! +${bet*2}</span>`;
                triggerHaptic('success');
            } else {
                res.innerHTML = `<span style="color:var(--accent-red);">🎲 Выпало ${roll}. Мимо</span>`;
                triggerHaptic('error');
            }
        }

        /* --- МОНЕТКА --- */
        let selectedCoin = 'heads';
        function selectCoin(val) {
            selectedCoin = val;
            document.querySelectorAll('#game-coin .flex-btns button').forEach(b => b.classList.remove('selected'));
            document.getElementById(`coin-${val}`).classList.add('selected');
        }
        function playCoin() {
            let bet = parseInt(document.getElementById('coinBet').value);
            if (bet > balance || bet <= 0) return alert('Недостаточно средств!');
            updateBalance(-bet); triggerHaptic('medium');
            let resVal = Math.random() < 0.5 ? 'heads' : 'tails';
            let res = document.getElementById('coinResult');
            if(resVal === selectedCoin) {
                updateBalance(bet * 2);
                res.innerHTML = `<span style="color:var(--accent-green);">🪙 ${resVal === 'heads' ? 'ОРЕЛ' : 'РЕШКА'}! +${bet*2}</span>`;
                triggerHaptic('success');
            } else {
                res.innerHTML = `<span style="color:var(--accent-red);">🪙 Выпал ${resVal === 'heads' ? 'ОРЕЛ' : 'РЕШКА'}. Проигрыш</span>`;
                triggerHaptic('error');
            }
        }

        /* --- 1. ПЛИНКО --- */
        function playPlinko() {
            let bet = parseInt(document.getElementById('plinkoBet').value);
            if (bet > balance || bet <= 0) return alert('Недостаточно средств!');
            updateBalance(-bet); triggerHaptic('medium');
            let mults = [0.2, 0.5, 2, 5, 10];
            let chosen = mults[Math.floor(Math.random() * mults.length)];
            let win = Math.floor(bet * chosen);
            updateBalance(win);
            let res = document.getElementById('plinkoResult');
            if(chosen >= 1) {
                res.innerHTML = `<span style="color:var(--accent-green);">🔺 Множитель x${chosen}! Выигрыш +${win}</span>`;
                triggerHaptic('success');
            } else {
                res.innerHTML = `<span style="color:var(--accent-red);">🔺 Множитель x${chosen}. Возврат ${win}</span>`;
                triggerHaptic('error');
            }
        }

        /* --- 2. ХАЙ-ЛО --- */
        let hiloCurrent = Math.floor(Math.random() * 10) + 2;
        function playHilo(guess) {
            let bet = parseInt(document.getElementById('hiloBet').value);
            if (bet > balance || bet <= 0) return alert('Недостаточно средств!');
            updateBalance(-bet); triggerHaptic('medium');
            let next = Math.floor(Math.random() * 10) + 2;
            document.getElementById('hiloCard').innerText = '🎴 ' + next;
            let win = (guess === 'higher' && next > hiloCurrent) || (guess === 'lower' && next < hiloCurrent);
            let res = document.getElementById('hiloResult');
            if(win) {
                updateBalance(bet * 1.8);
                res.innerHTML = `<span style="color:var(--accent-green);">📈 Угадали! +${Math.floor(bet*1.8)}</span>`;
                triggerHaptic('success');
            } else {
                res.innerHTML = `<span style="color:var(--accent-red);">📉 Не угадали! Проигрыш</span>`;
                triggerHaptic('error');
            }
            hiloCurrent = next;
        }

        /* --- 3. КОЛЕСО ФОРТУНЫ --- */
        function playWheel() {
            let bet = parseInt(document.getElementById('wheelBet').value);
            if (bet > balance || bet <= 0) return alert('Недостаточно средств!');
            updateBalance(-bet); triggerHaptic('heavy');
            let wheel = document.getElementById('fortuneWheel');
            let randomRot = Math.floor(Math.random() * 1440) + 720;
            wheel.style.transform = `rotate(${randomRot}deg)`;
            setTimeout(() => {
                let mults = [0, 2, 1, 5, 0, 3];
                let m = mults[Math.floor(Math.random() * mults.length)];
                let res = document.getElementById('wheelResult');
                if(m > 0) {
                    let win = bet * m; updateBalance(win);
                    res.innerHTML = `<span style="color:var(--accent-gold);">🎯 Сектор x${m}! Выигрыш +${win}</span>`;
                    triggerHaptic('success');
                } else {
                    res.innerHTML = `<span style="color:var(--accent-red);">🎯 Сектор БОНУС-НОЛЬ. Мимо</span>`;
                    triggerHaptic('error');
                }
            }, 3000);
        }

        /* --- 4. КЕНО --- */
        function playKeno() {
            let bet = parseInt(document.getElementById('kenoBet').value);
            if (bet > balance || bet <= 0) return alert('Недостаточно средств!');
            updateBalance(-bet); triggerHaptic('medium');
            let drawn = [];
            while(drawn.length < 3) { let n = Math.floor(Math.random()*10)+1; if(!drawn.includes(n)) drawn.push(n); }
            document.getElementById('kenoDrawn').innerText = drawn.join(', ');
            let res = document.getElementById('kenoResult');
            if(drawn.includes(7)) {
                let win = bet * 4; updateBalance(win);
                res.innerHTML = `<span style="color:var(--accent-green);">🔢 Совпало число 7! +${win}</span>`;
                triggerHaptic('success');
            } else {
                res.innerHTML = `<span style="color:var(--accent-red);">🔢 Тираж мимо кассы</span>`;
                triggerHaptic('error');
            }
        }

        /* --- 5. СКРЕТЧ-КАРТЫ --- */
        let scratchItems = ['💎', '💎', '🍒', '🍋'];
        function startScratch() {
            let bet = parseInt(document.getElementById('scratchBet').value);
            if (bet > balance || bet <= 0) return alert('Недостаточно средств!');
            updateBalance(-bet); triggerHaptic('light');
            scratchItems.sort(() => Math.random() - 0.5);
            for(let i=0; i<4; i++) {
                let el = document.getElementById(`sc${i}`);
                el.innerText = '❓'; el.classList.remove('revealed');
            }
            document.getElementById('scratchResult').innerText = 'Сотрите ячейки на карточке';
        }
        function revealScratch(idx) {
            let el = document.getElementById(`sc${idx}`);
            if(el.classList.contains('revealed')) return;
            el.innerText = scratchItems[idx];
            el.classList.add('revealed');
            triggerHaptic('light');
            
            // Проверка на 2 кристалла
            let revealedCount = document.querySelectorAll('.scratch-card-item.revealed').length;
            if(revealedCount === 4) {
                let countGems = scratchItems.filter(x => x === '💎').length;
                let bet = parseInt(document.getElementById('scratchBet').value);
                let res = document.getElementById('scratchResult');
                if(countGems >= 2) {
                    let win = bet * 3; updateBalance(win);
                    res.innerHTML = `<span style="color:var(--accent-green);">🎫 Найдено алмазов! +${win}</span>`;
                    triggerHaptic('success');
                } else {
                    res.innerHTML = `<span style="color:var(--accent-red);">🎫 Пустая карточка</span>`;
                    triggerHaptic('error');
                }
            }
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
            [InlineKeyboardButton(text="🎰 Открыть Casino Royale", web_app=WebAppInfo(url=WEBAPP_URL))]
        ]
    )
    await message.answer(
        "🎰 **Добро пожаловать в Grand Royale Casino!**\n\n"
        "Теперь доступно **12 потрясающих игр** с плавной анимацией и тактильной отдачей.\n\n"
        "Вы можете вызывать казино прямо через Inline-режим в любом чате!",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@router.inline_query()
async def inline_handler(query: InlineQuery):
    add_user(query.from_user.id)
    articles = [
        InlineQueryResultArticle(
            id="casino_app",
            title="🎰 Casino Royale (12 Игр)",
            description="Слоты, Рулетка, Плинко, Колесо Фортуны и многое другое!",
            input_message_content=InputTextMessageContent(
                message_text="🎰 Я открыл игровой зал казино! Присоединяйся к игре."
            ),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🎲 Играть в казино", web_app=WebAppInfo(url=WEBAPP_URL))]
                ]
            )
        )
    ]
    await query.answer(articles, cache_time=1, is_personal=True)

# --- ЗАПУСК БОТА И ВЕБ-СЕРВЕРА ---
async def main():
    init_db()
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    app = web.Application()
    app.router.add_get("/", handle_webapp)
    app.router.add_get("/webapp", handle_webapp)

    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    print(f"Бот и веб-сервер успешно запущены на порту {port}!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
