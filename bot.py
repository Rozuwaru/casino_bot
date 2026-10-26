import asyncio
import logging
import os
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

TOKEN = "8752641180:AAET94FACuNdO26CCdFHFyv1vJhSiv3O7F4"
WEBAPP_URL = "https://casino-bot-y2qo.onrender.com/webapp"

SUPABASE_URL = "https://lnskcqunuaewqcsvcpvr.supabase.co"
SUPABASE_KEY = "yJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imxuc2tjcXVudWFld3Fjc3ZjcHZyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTMwMzE2MjQsImV4cCI6MjEwODYwNzYyNH0.g0F_E6hIOeholtABi_WsbMzqT4H-49wTH5XYXAk_0Nc"

WEBAPP_HTML = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Grand Royale Casino</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #060810;
            --card-bg: #101426;
            --card-hover: #181f38;
            --accent-gold: #f39c12;
            --accent-gold-glow: rgba(243, 156, 18, 0.4);
            --accent-red: #c0392b;
            --accent-green: #27ae60;
            --text-main: #ffffff;
            --text-dim: #7f8c8d;
            --border-color: rgba(255, 255, 255, 0.1);
        }}
        * {{ box-sizing: border-box; user-select: none; -webkit-user-select: none; -webkit-tap-highlight-color: transparent; }}
        body {{ background-color: var(--bg-color); color: var(--text-main); font-family: 'Outfit', sans-serif; margin: 0; padding: 14px; min-height: 100vh; display: flex; flex-direction: column; align-items: center; background-image: radial-gradient(circle at top, #151b3b 0%, #060810 100%); }}

        .header {{ width: 100%; max-width: 440px; display: flex; justify-content: space-between; align-items: center; background: rgba(16, 20, 38, 0.9); padding: 12px 18px; border-radius: 18px; border: 1px solid var(--border-color); box-shadow: 0 10px 30px rgba(0,0,0,0.6); margin-bottom: 16px; backdrop-filter: blur(10px); }}
        .logo {{ font-weight: 800; font-size: 17px; color: var(--accent-gold); text-transform: uppercase; letter-spacing: 1px; text-shadow: 0 0 12px var(--accent-gold-glow); }}
        .balance-box {{ background: rgba(39, 174, 96, 0.15); border: 1px solid rgba(39, 174, 96, 0.4); padding: 6px 14px; border-radius: 12px; font-weight: 700; color: var(--accent-green); font-size: 14px; box-shadow: 0 0 12px rgba(39,174,96,0.2); transition: transform 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275); }}
        .balance-box.pulse {{ transform: scale(1.12); }}

        .container {{ width: 100%; max-width: 440px; }}
        .back-btn {{ background: var(--card-bg); color: var(--text-main); border: 1px solid var(--border-color); padding: 8px 16px; border-radius: 12px; font-weight: 600; cursor: pointer; margin-bottom: 14px; display: inline-flex; align-items: center; gap: 6px; }}
        .back-btn:active {{ transform: scale(0.95); background: var(--card-hover); }}

        .lobby-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; animation: fadeIn 0.3s ease; }}
        .game-card {{ background: linear-gradient(145deg, #13192f, #0b0f1e); border-radius: 20px; padding: 16px 12px; text-align: center; border: 1px solid var(--border-color); cursor: pointer; transition: all 0.25s ease; box-shadow: 0 8px 20px rgba(0,0,0,0.3); }}
        .game-card:hover, .game-card:active {{ transform: translateY(-4px); border-color: var(--accent-gold); box-shadow: 0 10px 25px var(--accent-gold-glow); }}
        .game-icon {{ font-size: 34px; margin-bottom: 6px; display: block; filter: drop-shadow(0 3px 6px rgba(0,0,0,0.4)); }}
        .game-title {{ font-size: 14px; font-weight: 700; margin-bottom: 2px; }}
        .game-desc {{ font-size: 10px; color: var(--text-dim); }}

        .game-screen {{ display: none; background: var(--card-bg); border-radius: 22px; padding: 20px 16px; border: 1px solid var(--border-color); box-shadow: 0 20px 40px rgba(0,0,0,0.8); text-align: center; animation: slideUp 0.3s ease; position: relative; }}
        .game-screen.active {{ display: block; }}

        @keyframes fadeIn {{ from {{ opacity: 0; transform: scale(0.96); }} to {{ opacity: 1; transform: scale(1); }} }}
        @keyframes slideUp {{ from {{ opacity: 0; transform: translateY(15px); }} to {{ opacity: 1; transform: translateY(0); }} }}

        .bet-control {{ margin: 14px 0; display: flex; gap: 8px; justify-content: center; align-items: center; background: rgba(0,0,0,0.3); padding: 6px 10px; border-radius: 14px; border: 1px solid var(--border-color); }}
        .bet-control label {{ font-size: 12px; color: var(--text-dim); font-weight: 600; }}
        .bet-input {{ width: 80px; background: transparent; border: none; color: var(--accent-gold); font-weight: 800; font-size: 16px; text-align: center; outline: none; }}

        .action-btn {{ background: linear-gradient(135deg, #f39c12, #d35400); color: #fff; border: none; width: 100%; padding: 14px; font-size: 15px; font-weight: 800; border-radius: 14px; cursor: pointer; transition: all 0.2s ease; box-shadow: 0 6px 18px rgba(243, 156, 18, 0.3); text-transform: uppercase; letter-spacing: 0.8px; }}
        .action-btn:active {{ transform: scale(0.97); opacity: 0.9; }}

        .result-box {{ margin-top: 12px; font-weight: 700; min-height: 24px; font-size: 15px; }}
        .flex-btns {{ display: flex; gap: 6px; margin-bottom: 10px; }}
        .flex-btns button {{ flex: 1; padding: 10px 6px; background: var(--card-hover); border: 1px solid var(--border-color); color: var(--text-main); border-radius: 10px; font-weight: 600; font-size: 12px; cursor: pointer; transition: 0.2s; }}
        .flex-btns button.selected {{ border-color: var(--accent-gold); background: rgba(243, 156, 18, 0.2); color: var(--accent-gold); box-shadow: 0 0 8px rgba(243, 156, 18, 0.2); }}

        /* СЛОТЫ */
        .slots-window {{ display: flex; justify-content: center; gap: 10px; background: #000; padding: 12px; border-radius: 16px; border: 2px solid var(--accent-gold); margin: 12px 0; box-shadow: inset 0 0 20px rgba(0,0,0,0.9), 0 0 15px var(--accent-gold-glow); overflow: hidden; height: 110px; align-items: center; }}
        .reel-container {{ width: 65px; height: 85px; overflow: hidden; background: linear-gradient(180deg, #000 0%, #1a1a1a 50%, #000 100%); border-radius: 10px; border: 1px solid var(--border-color); position: relative; }}
        .reel-strip {{ display: flex; flex-direction: column; align-items: center; position: absolute; width: 100%; top: 0; }}
        .symbol {{ width: 65px; height: 85px; display: flex; align-items: center; justify-content: center; font-size: 38px; }}

        /* РУЛЕТКА CANVAS */
        .roulette-canvas-box {{ position: relative; width: 220px; height: 220px; margin: 10px auto; }}
        canvas {{ display: block; margin: 0 auto; border-radius: 50%; box-shadow: 0 0 25px rgba(0,0,0,0.8); }}

        /* КАРТЫ */
        .card-box {{ display: inline-flex; align-items: center; justify-content: center; width: 48px; height: 68px; background: #fff; color: #000; border-radius: 6px; font-weight: 800; font-size: 18px; box-shadow: 0 4px 8px rgba(0,0,0,0.4); }}
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">🎰 Casino Royale</div>
        <div class="balance-box" id="balanceBox">🪙 <span id="userBalance">1000</span></div>
    </div>
    <div class="container">
        <!-- ЛОББИ -->
        <div id="lobby" class="lobby-grid">
            <div class="game-card" onclick="openGame('slots')"><span class="game-icon">🎰</span><div class="game-title">Слоты 777</div><div class="game-desc">Барабаны 3D</div></div>
            <div class="game-card" onclick="openGame('roulette')"><span class="game-icon">🎡</span><div class="game-title">Рулетка</div><div class="game-desc">Европейская</div></div>
            <div class="game-card" onclick="openGame('blackjack')"><span class="game-icon">🃏</span><div class="game-title">Блэкджек</div><div class="game-desc">Карты до 21</div></div>
            <div class="game-card" onclick="openGame('mines')"><span class="game-icon">💣</span><div class="game-title">Минное поле</div><div class="game-desc">Кристаллы</div></div>
            <div class="game-card" onclick="openGame('crash')"><span class="game-icon">🚀</span><div class="game-title">Краш X</div><div class="game-desc">Ракета x100</div></div>
            <div class="game-card" onclick="openGame('dice')"><span class="game-icon">🎲</span><div class="game-title">Кости</div><div class="game-desc">Кубик удачи</div></div>
            <div class="game-card" onclick="openGame('coin')"><span class="game-icon">🪙</span><div class="game-title">Монетка</div><div class="game-desc">Орел / Решка</div></div>
            <div class="game-card" onclick="openGame('plinko')"><span class="game-icon">🔺</span><div class="game-title">Плинко</div><div class="game-desc">Пирамида шаров</div></div>
            <div class="game-card" onclick="openGame('hilo')"><span class="game-icon">📈</span><div class="game-title">Хай-Ло</div><div class="game-desc">Выше / Ниже</div></div>
            <div class="game-card" onclick="openGame('wheel')"><span class="game-icon">🎯</span><div class="game-title">Колесо Фортуны</div><div class="game-desc">Множители</div></div>
            <div class="game-card" onclick="openGame('keno')"><span class="game-icon">🔢</span><div class="game-title">Кено</div><div class="game-desc">Тираж лотереи</div></div>
            <div class="game-card" onclick="openGame('scratch')"><span class="game-icon">🎫</span><div class="game-title">Скретч-карты</div><div class="game-desc">Стирай билет</div></div>
        </div>

        <!-- 1. СЛОТЫ -->
        <div id="game-slots" class="game-screen">
            <button class="back-btn" onclick="showLobby()">⬅ Назад</button>
            <h3>🎰 Слоты 777</h3>
            <div class="slots-window">
                <div class="reel-container"><div class="reel-strip" id="strip1"></div></div>
                <div class="reel-container"><div class="reel-strip" id="strip2"></div></div>
                <div class="reel-container"><div class="reel-strip" id="strip3"></div></div>
            </div>
            <div class="bet-control"><label>Ставка:</label><input type="number" id="slotsBet" class="bet-input" value="100" min="10"></div>
            <button class="action-btn" id="slotsBtn" onclick="playSlots()">Крутить барабаны</button>
            <div class="result-box" id="slotsResult"></div>
        </div>

        <!-- 2. РУЛЕТКА -->
        <div id="game-roulette" class="game-screen">
            <button class="back-btn" onclick="showLobby()">⬅ Назад</button>
            <h3>🎡 Европейская Рулетка</h3>
            <div class="roulette-canvas-box">
                <canvas id="rouletteCanvas" width="220" height="220"></canvas>
            </div>
            <div class="flex-btns" style="margin-top: 10px;">
                <button id="roul-red" onclick="selectRoulette('red')" class="selected">🔴 Красное (x2)</button>
                <button id="roul-black" onclick="selectRoulette('black')">⚫ Черное (x2)</button>
                <button id="roul-zero" onclick="selectRoulette('zero')">🟢 Зеро (x14)</button>
            </div>
            <div class="bet-control"><label>Ставка:</label><input type="number" id="rouletteBet" class="bet-input" value="100" min="10"></div>
            <button class="action-btn" id="roulBtn" onclick="playRoulette()">Вращать рулетку</button>
            <div class="result-box" id="rouletteResult"></div>
        </div>

        <!-- 3. БЛЭКДЖЕК -->
        <div id="game-blackjack" class="game-screen">
            <button class="back-btn" onclick="showLobby()">⬅ Назад</button>
            <h3>🃏 Блэкджек 21</h3>
            <div style="background:rgba(0,0,0,0.3); padding:12px; border-radius:14px; margin:12px 0; border:1px solid var(--border-color);">
                <div>Дилер (<span id="bjDealerScore">0</span>):</div>
                <div style="display:flex; gap:6px; justify-content:center; margin:6px 0;" id="bjDealerCards"></div>
                <hr style="border-color:var(--border-color); margin:8px 0;">
                <div>Вы (<span id="bjPlayerScore">0</span>):</div>
                <div style="display:flex; gap:6px; justify-content:center; margin:6px 0;" id="bjPlayerCards"></div>
            </div>
            <div class="bet-control"><label>Ставка:</label><input type="number" id="bjBet" class="bet-input" value="100" min="10"></div>
            <div class="flex-btns" id="bjControls" style="display:none;">
                <button onclick="bjHit()" style="background:#27ae60; color:#fff;">Взять карту</button>
                <button onclick="bjStand()" style="background:#c0392b; color:#fff;">Хватит</button>
            </div>
            <button class="action-btn" id="bjStartBtn" onclick="startBlackjack()">Раздать карты</button>
            <div class="result-box" id="bjResult"></div>
        </div>

        <!-- 4. МИННОЕ ПОЛЕ -->
        <div id="game-mines" class="game-screen">
            <button class="back-btn" onclick="showLobby()">⬅ Назад</button>
            <h3>💣 Минное поле</h3>
            <div id="minesGrid" style="display:grid; grid-template-columns:repeat(5, 1fr); gap:6px; margin:14px 0;"></div>
            <div class="bet-control"><label>Ставка:</label><input type="number" id="minesBet" class="bet-input" value="100" min="10"></div>
            <button class="action-btn" id="minesStartBtn" onclick="startMines()">Начать игру</button>
            <button class="action-btn" id="minesCashoutBtn" onclick="cashoutMines()" style="display:none; background:#27ae60; margin-top:8px;">Забрать выигрыш</button>
            <div class="result-box" id="minesResult"></div>
        </div>

        <!-- 5. КРАШ -->
        <div id="game-crash" class="game-screen">
            <button class="back-btn" onclick="showLobby()">⬅ Назад</button>
            <h3>🚀 Краш X</h3>
            <div style="background:#000; height:110px; border-radius:14px; display:flex; align-items:center; justify-content:center; font-size:40px; font-weight:800; color:var(--accent-gold); margin:14px 0; border:1px solid var(--accent-gold); box-shadow:0 0 15px rgba(243,156,18,0.2);" id="crashDisplay">1.00x</div>
            <div class="bet-control"><label>Ставка:</label><input type="number" id="crashBet" class="bet-input" value="100" min="10"></div>
            <button class="action-btn" id="crashBtn" onclick="startCrash()">Запустить ракету</button>
            <div class="result-box" id="crashResult"></div>
        </div>

        <!-- 6. КОСТИ -->
        <div id="game-dice" class="game-screen">
            <button class="back-btn" onclick="showLobby()">⬅ Назад</button>
            <h3>🎲 Кости</h3>
            <div style="font-size:55px; margin:16px 0; transition: transform 0.3s;" id="diceIcon">🎲</div>
            <div class="flex-btns">
                <button id="dice-low" onclick="selectDice('low')" class="selected">Меньше 4 (x2)</button>
                <button id="dice-high" onclick="selectDice('high')">Больше 3 (x2)</button>
            </div>
            <div class="bet-control"><label>Ставка:</label><input type="number" id="diceBet" class="bet-input" value="100" min="10"></div>
            <button class="action-btn" onclick="playDice()">Бросить кости</button>
            <div class="result-box" id="diceResult"></div>
        </div>

        <!-- 7. МОНЕТКА -->
        <div id="game-coin" class="game-screen">
            <button class="back-btn" onclick="showLobby()">⬅ Назад</button>
            <h3>🪙 Монетка</h3>
            <div style="font-size:55px; margin:16px 0; transition: transform 0.4s;" id="coinIcon">🪙</div>
            <div class="flex-btns">
                <button id="coin-heads" onclick="selectCoin('heads')" class="selected">🦅 Орел</button>
                <button id="coin-tails" onclick="selectCoin('tails')">🪙 Решка</button>
            </div>
            <div class="bet-control"><label>Ставка:</label><input type="number" id="coinBet" class="bet-input" value="100" min="10"></div>
            <button class="action-btn" onclick="playCoin()">Подбросить</button>
            <div class="result-box" id="coinResult"></div>
        </div>

        <!-- 8. ПЛИНКО -->
        <div id="game-plinko" class="game-screen">
            <button class="back-btn" onclick="showLobby()">⬅ Назад</button>
            <h3>🔺 Плинко</h3>
            <div style="display:grid; grid-template-columns:repeat(5, 1fr); gap:6px; margin:14px 0;">
                <div style="background:rgba(255,255,255,0.05); padding:8px; border-radius:8px; font-size:11px; font-weight:700; color:var(--accent-gold);">0.2x</div>
                <div style="background:rgba(255,255,255,0.05); padding:8px; border-radius:8px; font-size:11px; font-weight:700; color:var(--accent-gold);">0.5x</div>
                <div style="background:rgba(255,255,255,0.05); padding:8px; border-radius:8px; font-size:11px; font-weight:700; color:var(--accent-gold);">2x</div>
                <div style="background:rgba(255,255,255,0.05); padding:8px; border-radius:8px; font-size:11px; font-weight:700; color:var(--accent-gold);">5x</div>
                <div style="background:rgba(255,255,255,0.05); padding:8px; border-radius:8px; font-size:11px; font-weight:700; color:var(--accent-gold);">10x</div>
            </div>
            <div class="bet-control"><label>Ставка:</label><input type="number" id="plinkoBet" class="bet-input" value="100" min="10"></div>
            <button class="action-btn" onclick="playPlinko()">Запустить шар</button>
            <div class="result-box" id="plinkoResult"></div>
        </div>

        <!-- 9. ХАЙ-ЛО -->
        <div id="game-hilo" class="game-screen">
            <button class="back-btn" onclick="showLobby()">⬅ Назад</button>
            <h3>📈 Хай-Ло</h3>
            <div style="margin:16px 0; display:flex; justify-content:center;">
                <div class="card-box" id="hiloCard" style="width:60px; height:85px; font-size:24px;">7</div>
            </div>
            <div class="flex-btns">
                <button onclick="playHilo('lower')">📉 Ниже</button>
                <button onclick="playHilo('higher')">📈 Выше</button>
            </div>
            <div class="bet-control"><label>Ставка:</label><input type="number" id="hiloBet" class="bet-input" value="100" min="10"></div>
            <div class="result-box" id="hiloResult">Угадайте карту</div>
        </div>

        <!-- 10. КОЛЕСО ФОРТУНЫ -->
        <div id="game-wheel" class="game-screen">
            <button class="back-btn" onclick="showLobby()">⬅ Назад</button>
            <h3>🎯 Колесо Фортуны</h3>
            <div class="roulette-canvas-box">
                <canvas id="wheelCanvas" width="220" height="220"></canvas>
            </div>
            <div class="bet-control" style="margin-top: 10px;"><label>Ставка:</label><input type="number" id="wheelBet" class="bet-input" value="100" min="10"></div>
            <button class="action-btn" onclick="playWheel()">Крутить колесо</button>
            <div class="result-box" id="wheelResult"></div>
        </div>

        <!-- 11. КЕНО -->
        <div id="game-keno" class="game-screen">
            <button class="back-btn" onclick="showLobby()">⬅ Назад</button>
            <h3>🔢 Кено Лото</h3>
            <div style="font-size:12px; color:var(--text-dim); margin-bottom:8px;">Выпало чисел: <span id="kenoDrawn" style="color:var(--accent-gold); font-weight:bold;">-</span></div>
            <div class="bet-control"><label>Ставка:</label><input type="number" id="kenoBet" class="bet-input" value="100" min="10"></div>
            <button class="action-btn" onclick="playKeno()">Розыгрыш тиража</button>
            <div class="result-box" id="kenoResult"></div>
        </div>

        <!-- 12. СКРЕТЧ-КАРТЫ -->
        <div id="game-scratch" class="game-screen">
            <button class="back-btn" onclick="showLobby()">⬅ Назад</button>
            <h3>🎫 Скретч-карты</h3>
            <div style="display:grid; grid-template-columns:repeat(2, 1fr); gap:8px; margin:14px 0;" id="scratchGrid">
                <div style="background:rgba(255,255,255,0.04); border-radius:12px; height:65px; display:flex; align-items:center; justify-content:center; font-size:26px; cursor:pointer;" onclick="revealScratch(0)" id="sc0">❓</div>
                <div style="background:rgba(255,255,255,0.04); border-radius:12px; height:65px; display:flex; align-items:center; justify-content:center; font-size:26px; cursor:pointer;" onclick="revealScratch(1)" id="sc1">❓</div>
                <div style="background:rgba(255,255,255,0.04); border-radius:12px; height:65px; display:flex; align-items:center; justify-content:center; font-size:26px; cursor:pointer;" onclick="revealScratch(2)" id="sc2">❓</div>
                <div style="background:rgba(255,255,255,0.04); border-radius:12px; height:65px; display:flex; align-items:center; justify-content:center; font-size:26px; cursor:pointer;" onclick="revealScratch(3)" id="sc3">❓</div>
            </div>
            <div class="bet-control"><label>Ставка:</label><input type="number" id="scratchBet" class="bet-input" value="100" min="10"></div>
            <button class="action-btn" onclick="startScratch()">Новый билет</button>
            <div class="result-box" id="scratchResult">Сотрите билет</div>
        </div>
    </div>

    <script>
        const tg = window.Telegram.WebApp;
        tg.expand();

        const _supabase = supabase.createClient("{SUPABASE_URL}", "{SUPABASE_KEY}");
        let userId = tg.initDataUnsafe?.user?.id || Math.floor(Math.random() * 1000000);
        let balance = 1000;

        async function loadUserBalance() {{
            try {{
                let {{ data, error }} = await _supabase.from('users').select('balance').eq('user_id', userId).single();
                if (data) {{
                    balance = data.balance;
                }} else {{
                    await _supabase.from('users').insert([{{ user_id: userId, balance: 1000 }}]);
                    balance = 1000;
                }}
                document.getElementById('userBalance').innerText = balance;
            }} catch (e) {{
                console.error("Supabase load error:", e);
                document.getElementById('userBalance').innerText = balance;
            }}
        }}

        async function updateBalance(amount) {{
            balance += amount;
            let el = document.getElementById('userBalance');
            let box = document.getElementById('balanceBox');
            el.innerText = balance;
            box.classList.add('pulse');
            setTimeout(() => box.classList.remove('pulse'), 200);
            try {{
                await _supabase.from('users').update({{ balance: balance }}).eq('user_id', userId);
            }} catch (e) {{
                console.error("Supabase update error:", e);
            }}
        }}

        loadUserBalance();

        function triggerHaptic(type = 'medium') {{
            if (tg.HapticFeedback) {{
                if (type === 'success') tg.HapticFeedback.notificationOccurred('success');
                else if (type === 'error') tg.HapticFeedback.notificationOccurred('error');
                else tg.HapticFeedback.impactOccurred(type);
            }}
        }}

        function showLobby() {{
            document.querySelectorAll('.game-screen').forEach(el => el.classList.remove('active'));
            document.getElementById('lobby').style.display = 'grid';
        }}

        function openGame(gameId) {{
            triggerHaptic('light');
            document.getElementById('lobby').style.display = 'none';
            document.getElementById(`game-${{gameId}}`).classList.add('active');
            if(gameId === 'roulette') drawRouletteWheel(0);
            if(gameId === 'wheel') drawFortuneWheel(0);
        }}

        /* --- 1. РУЛЕТКА CANVAS --- */
        const rouletteNumbers = [0,32,15,19,4,21,2,25,17,34,6,27,13,36,11,30,8,23,10,5,24,16,33,1,20,14,31,9,22,18,29,7,28,12,35,3,26];
        function drawRouletteWheel(angle) {{
            const canvas = document.getElementById('rouletteCanvas');
            if(!canvas) return;
            const ctx = canvas.getContext('2d');
            const rad = canvas.width / 2;
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.save();
            ctx.translate(rad, rad);
            ctx.rotate(angle);

            const slice = (2 * Math.PI) / rouletteNumbers.length;
            for(let i=0; i<rouletteNumbers.length; i++) {{
                ctx.beginPath();
                ctx.moveTo(0,0);
                ctx.arc(0, 0, rad - 5, i * slice, (i + 1) * slice);
                ctx.fillStyle = rouletteNumbers[i] === 0 ? '#27ae60' : (i % 2 === 0 ? '#c0392b' : '#111');
                ctx.fill();
                ctx.lineWidth = 1;
                ctx.strokeStyle = '#f39c12';
                ctx.stroke();

                ctx.save();
                ctx.rotate(i * slice + slice / 2);
                ctx.textAlign = "right";
                ctx.fillStyle = "#fff";
                ctx.font = "bold 10px Outfit";
                ctx.fillText(rouletteNumbers[i], rad - 12, 4);
                ctx.restore();
            }}
            ctx.restore();

            // Указатель сверху
            ctx.fillStyle = "#fff";
            ctx.beginPath();
            ctx.moveTo(rad - 6, 0);
            ctx.lineTo(rad + 6, 0);
            ctx.lineTo(rad, 12);
            ctx.fill();
        }}

        let selectedRoulette = 'red';
        function selectRoulette(val) {{
            selectedRoulette = val;
            document.querySelectorAll('#game-roulette .flex-btns button').forEach(b => b.classList.remove('selected'));
            document.getElementById(`roul-${{val}}`).classList.add('selected');
        }}
        function playRoulette() {{
            let bet = parseInt(document.getElementById('rouletteBet').value);
            if (bet > balance || bet <= 0) return alert('Недостаточно средств!');
            updateBalance(-bet); triggerHaptic('heavy');
            
            let targetIdx = Math.floor(Math.random() * rouletteNumbers.length);
            let slice = (2 * Math.PI) / rouletteNumbers.length;
            let finalAngle = Math.PI * 10 - (targetIdx * slice + slice / 2);
            
            let startTime = null;
            let duration = 3000;
            function animateRoul(timestamp) {{
                if(!startTime) startTime = timestamp;
                let progress = (timestamp - startTime) / duration;
                if(progress > 1) progress = 1;
                let ease = 1 - Math.pow(1 - progress, 3);
                drawRouletteWheel(finalAngle * ease);
                if(progress < 1) {{
                    requestAnimationFrame(animateRoul);
                }} else {{
                    let num = rouletteNumbers[targetIdx];
                    let color = num === 0 ? 'zero' : ([32,19,21,25,34,27,36,30,23,5,16,1,14,9,18,7,35,3].includes(num) ? 'red' : 'black');
                    let resBox = document.getElementById('rouletteResult');
                    if (color === selectedRoulette) {{
                        let mult = selectedRoulette === 'zero' ? 14 : 2;
                        let win = bet * mult; updateBalance(win);
                        resBox.innerHTML = `<span style="color:var(--accent-green);">🎯 ${{num}} (${{color.toUpperCase()}})! +${{win}}</span>`;
                        triggerHaptic('success');
                    }} else {{
                        resBox.innerHTML = `<span style="color:var(--accent-red);">❌ ${{num}} (${{color.toUpperCase()}}). Проигрыш</span>`;
                        triggerHaptic('error');
                    }}
                }}
            }}
            requestAnimationFrame(animateRoul);
        }}

        /* --- 2. СЛОТЫ --- */
        const symbols = ['🍒', '🍋', '🔔', '💎', '7️⃣'];
        function buildReelStrip(stripId) {{
            const strip = document.getElementById(stripId);
            strip.innerHTML = '';
            for(let i=0; i<30; i++) {{
                const div = document.createElement('div');
                div.className = 'symbol';
                div.innerText = symbols[Math.floor(Math.random() * symbols.length)];
                strip.appendChild(div);
            }}
        }}
        buildReelStrip('strip1'); buildReelStrip('strip2'); buildReelStrip('strip3');

        let slotsActive = false;
        function playSlots() {{
            if (slotsActive) return;
            let bet = parseInt(document.getElementById('slotsBet').value);
            if (bet > balance || bet <= 0) return alert('Недостаточно средств!');
            slotsActive = true; updateBalance(-bet); triggerHaptic('heavy');
            document.getElementById('slotsBtn').disabled = true;

            const res1 = symbols[Math.floor(Math.random() * symbols.length)];
            const res2 = symbols[Math.floor(Math.random() * symbols.length)];
            const res3 = symbols[Math.floor(Math.random() * symbols.length)];

            function animateReel(stripId, targetSymbol, delay) {{
                return new Promise(resolve => {{
                    const strip = document.getElementById(stripId);
                    buildReelStrip(stripId);
                    strip.children[27].innerText = targetSymbol;
                    strip.style.transition = 'none';
                    strip.style.transform = 'translateY(0px)';
                    setTimeout(() => {{
                        strip.style.transition = `transform ${{2 + delay}}s cubic-bezier(0.1, 0.8, 0.3, 1)`;
                        strip.style.transform = `translateY(-${{27 * 85}}px)`;
                        setTimeout(resolve, (2 + delay) * 1000);
                    }}, 50);
                }});
            }}

            Promise.all([
                animateReel('strip1', res1, 0),
                animateReel('strip2', res2, 0.3),
                animateReel('strip3', res3, 0.6)
            ]).then(() => {{
                slotsActive = false; document.getElementById('slotsBtn').disabled = false;
                let resBox = document.getElementById('slotsResult');
                if (res1 === res2 && res2 === res3) {{
                    let win = bet * 5; updateBalance(win);
                    resBox.innerHTML = `<span style="color:var(--accent-gold);">🎉 ДЖЕКПОТ! +${{win}}</span>`;
                    triggerHaptic('success');
                }} else if (res1 === res2 || res2 === res3 || res1 === res3) {{
                    let win = Math.floor(bet * 1.5); updateBalance(win);
                    resBox.innerHTML = `<span style="color:var(--accent-green);">✨ Пара! +${{win}}</span>`;
                    triggerHaptic('success');
                }} else {{
                    resBox.innerHTML = `<span style="color:var(--accent-red);">😢 Мимо...</span>`;
                    triggerHaptic('error');
                }}
            }});
        }}

        /* --- 3. БЛЭКДЖЕК --- */
        let bjState = {{ player: [], dealer: [], playing: false }};
        function getCard() {{ return Math.min(10, Math.floor(Math.random() * 10) + 2); }}
        function sumHand(h) {{ return h.reduce((a,b)=>a+b, 0); }}
        function startBlackjack() {{
            let bet = parseInt(document.getElementById('bjBet').value);
            if (bet > balance || bet <= 0) return alert('Недостаточно средств!');
            updateBalance(-bet); triggerHaptic('medium');
            bjState = {{ player: [getCard(), getCard()], dealer: [getCard()], playing: true }};
            document.getElementById('bjStartBtn').style.display = 'none';
            document.getElementById('bjControls').style.display = 'flex';
            document.getElementById('bjResult').innerText = '';
            renderBJ();
        }}
        function renderBJ() {{
            document.getElementById('bjPlayerCards').innerHTML = bjState.player.map(c => `<div class="card-box">${{c}}</div>`).join('');
            document.getElementById('bjDealerCards').innerHTML = bjState.dealer.map(c => `<div class="card-box">${{c}}</div>`).join('') + '<div class="card-box" style="background:#222; color:#fff;">🂠</div>';
            document.getElementById('bjPlayerScore').innerText = sumHand(bjState.player);
            document.getElementById('bjDealerScore').innerText = sumHand(bjState.dealer);
        }}
        function bjHit() {{
            if (!bjState.playing) return;
            bjState.player.push(getCard()); renderBJ();
            if (sumHand(bjState.player) > 21) endBJ(false, '💥 Перебор!');
        }}
        function bjStand() {{
            if (!bjState.playing) return;
            while(sumHand(bjState.dealer) < 17) bjState.dealer.push(getCard());
            let p = sumHand(bjState.player), d = sumHand(bjState.dealer);
            if (d > 21 || p > d) endBJ(true, '🎉 Победа!');
            else if (p === d) endBJ('draw', '🤝 Ничья!');
            else endBJ(false, '😢 Дилер выиграл!');
        }}
        function endBJ(win, msg) {{
            bjState.playing = false;
            let bet = parseInt(document.getElementById('bjBet').value);
            if (win === true) {{ updateBalance(bet * 2); triggerHaptic('success'); }}
            else if (win === 'draw') {{ updateBalance(bet); }}
            else {{ triggerHaptic('error'); }}
            document.getElementById('bjDealerCards').innerHTML = bjState.dealer.map(c => `<div class="card-box">${{c}}</div>`).join('');
            document.getElementById('bjDealerScore').innerText = sumHand(bjState.dealer);
            document.getElementById('bjResult').innerText = msg;
            document.getElementById('bjStartBtn').style.display = 'block';
            document.getElementById('bjControls').style.display = 'none';
        }}

        /* --- 4. МИНЫ --- */
        let minesState = {{ active: false, bombs: [], opened: 0, mult: 1.2 }};
        function startMines() {{
            let bet = parseInt(document.getElementById('minesBet').value);
            if (bet > balance || bet <= 0) return alert('Недостаточно средств!');
            updateBalance(-bet); triggerHaptic('medium');
            let grid = document.getElementById('minesGrid'); grid.innerHTML = '';
            let bombs = [];
            while(bombs.length < 3) {{ let r = Math.floor(Math.random()*25); if(!bombs.includes(r)) bombs.push(r); }}
            minesState = {{ active: true, bombs: bombs, opened: 0, mult: 1.2, bet: bet }};
            for(let i=0; i<25; i++) {{
                let tile = document.createElement('div');
                tile.style.cssText = "aspect-ratio:1; background:rgba(255,255,255,0.05); border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:16px; cursor:pointer;";
                tile.onclick = () => clickMine(i, tile);
                grid.appendChild(tile);
            }}
            document.getElementById('minesStartBtn').style.display = 'none';
            document.getElementById('minesCashoutBtn').style.display = 'block';
            document.getElementById('minesResult').innerText = '💎 Ищите кристаллы!';
        }}
        function clickMine(idx, tile) {{
            if(!minesState.active || tile.style.background.includes('rgb(39')) return;
            if(minesState.bombs.includes(idx)) {{
                tile.style.background = 'rgba(192,57,43,0.5)'; tile.innerText = '💣';
                minesState.active = false;
                document.getElementById('minesResult').innerHTML = '<span style="color:var(--accent-red);">💥 БУМ! Проигрыш</span>';
                document.getElementById('minesStartBtn').style.display = 'block';
                document.getElementById('minesCashoutBtn').style.display = 'none';
                triggerHaptic('error');
            }} else {{
                tile.style.background = 'rgba(39,174,96,0.4)'; tile.innerText = '💎';
                minesState.opened++; minesState.mult += 0.3;
                let cur = Math.floor(minesState.bet * minesState.mult);
                document.getElementById('minesResult').innerText = `💰 Профит: +${{cur}} (x${{minesState.mult.toFixed(2)}})`;
                triggerHaptic('light');
            }}
        }}
        function cashoutMines() {{
            if(!minesState.active || minesState.opened === 0) return;
            let win = Math.floor(minesState.bet * minesState.mult);
            updateBalance(win); minesState.active = false;
            document.getElementById('minesResult').innerHTML = `<span style="color:var(--accent-green);">💰 Забрал +${{win}}!</span>`;
            document.getElementById('minesStartBtn').style.display = 'block';
            document.getElementById('minesCashoutBtn').style.display = 'none';
            triggerHaptic('success');
        }}

        /* --- 5. КРАШ --- */
        let crashInterval = null;
        function startCrash() {{
            let bet = parseInt(document.getElementById('crashBet').value);
            if (bet > balance || bet <= 0) return alert('Недостаточно средств!');
            updateBalance(-bet); triggerHaptic('medium');
            let mult = 1.00, crashPoint = (Math.random() * 4 + 1).toFixed(2);
            let btn = document.getElementById('crashBtn'), display = document.getElementById('crashDisplay'), active = true;
            btn.innerText = 'Забрать';
            btn.onclick = () => {{
                if(!active) return;
                active = false; clearInterval(crashInterval);
                let win = Math.floor(bet * mult); updateBalance(win);
                document.getElementById('crashResult').innerHTML = `<span style="color:var(--accent-green);">🎉 Успел! +${{win}}</span>`;
                btn.innerText = 'Запустить ракету'; btn.onclick = startCrash; triggerHaptic('success');
            }};
            crashInterval = setInterval(() => {{
                mult += 0.05; display.innerText = mult.toFixed(2) + 'x';
                if(mult >= crashPoint && active) {{
                    active = false; clearInterval(crashInterval);
                    display.innerText = '💥 CRASH!';
                    document.getElementById('crashResult').innerHTML = `<span style="color:var(--accent-red);">😢 Улетел на ${{crashPoint}}x</span>`;
                    btn.innerText = 'Запустить ракету'; btn.onclick = startCrash; triggerHaptic('error');
                }}
            }}, 90);
        }}

        /* --- 6. КОСТИ --- */
        let selectedDice = 'low';
        function selectDice(val) {{
            selectedDice = val;
            document.querySelectorAll('#game-dice .flex-btns button').forEach(b => b.classList.remove('selected'));
            document.getElementById(`dice-${{val}}`).classList.add('selected');
        }}
        function playDice() {{
            let bet = parseInt(document.getElementById('diceBet').value);
            if (bet > balance || bet <= 0) return alert('Недостаточно средств!');
            updateBalance(-bet); triggerHaptic('medium');
            let roll = Math.floor(Math.random()*6)+1;
            let dice = document.getElementById('diceIcon');
            dice.style.transform = 'rotate(360deg)';
            setTimeout(() => dice.style.transform = 'rotate(0deg)', 300);

            let win = (selectedDice === 'low' && roll <= 3) || (selectedDice === 'high' && roll >= 4);
            let res = document.getElementById('diceResult');
            if(win) {{
                updateBalance(bet * 2);
                res.innerHTML = `<span style="color:var(--accent-green);">🎲 Выпало ${{roll}}! +${{bet*2}}</span>`;
                triggerHaptic('success');
            }} else {{
                res.innerHTML = `<span style="color:var(--accent-red);">🎲 Выпало ${{roll}}. Мимо</span>`;
                triggerHaptic('error');
            }}
        }}

        /* --- 7. МОНЕТКА --- */
        let selectedCoin = 'heads';
        function selectCoin(val) {{
            selectedCoin = val;
            document.querySelectorAll('#game-coin .flex-btns button').forEach(b => b.classList.remove('selected'));
            document.getElementById(`coin-${{val}}`).classList.add('selected');
        }}
        function playCoin() {{
            let bet = parseInt(document.getElementById('coinBet').value);
            if (bet > balance || bet <= 0) return alert('Недостаточно средств!');
            updateBalance(-bet); triggerHaptic('medium');
            let coin = document.getElementById('coinIcon');
            coin.style.transform = 'rotateY(720deg)';
            setTimeout(() => coin.style.transform = 'rotateY(0deg)', 400);

            let resVal = Math.random() < 0.5 ? 'heads' : 'tails';
            let res = document.getElementById('coinResult');
            if(resVal === selectedCoin) {{
                updateBalance(bet * 2);
                res.innerHTML = `<span style="color:var(--accent-green);">🪙 ${{resVal === 'heads' ? 'ОРЕЛ' : 'РЕШКА'}}! +${{bet*2}}</span>`;
                triggerHaptic('success');
            }} else {{
                res.innerHTML = `<span style="color:var(--accent-red);">🪙 Выпал ${{resVal === 'heads' ? 'ОРЕЛ' : 'РЕШКА'}}. Проигрыш</span>`;
                triggerHaptic('error');
            }}
        }}

        /* --- 8. ПЛИНКО --- */
        function playPlinko() {{
            let bet = parseInt(document.getElementById('plinkoBet').value);
            if (bet > balance || bet <= 0) return alert('Недостаточно средств!');
            updateBalance(-bet); triggerHaptic('medium');
            let mults = [0.2, 0.5, 2, 5, 10];
            let chosen = mults[Math.floor(Math.random() * mults.length)];
            let win = Math.floor(bet * chosen);
            updateBalance(win);
            let res = document.getElementById('plinkoResult');
            if(chosen >= 1) {{
                res.innerHTML = `<span style="color:var(--accent-green);">🔺 Множитель x${{chosen}}! +${{win}}</span>`;
                triggerHaptic('success');
            }} else {{
                res.innerHTML = `<span style="color:var(--accent-red);">🔺 Множитель x${{chosen}}. Возврат ${{win}}</span>`;
                triggerHaptic('error');
            }}
        }}

        /* --- 9. ХАЙ-ЛО --- */
        let hiloCurrent = Math.floor(Math.random() * 10) + 2;
        function playHilo(guess) {{
            let bet = parseInt(document.getElementById('hiloBet').value);
            if (bet > balance || bet <= 0) return alert('Недостаточно средств!');
            updateBalance(-bet); triggerHaptic('medium');
            let next = Math.floor(Math.random() * 10) + 2;
            document.getElementById('hiloCard').innerText = next;

            let win = (guess === 'higher' && next > hiloCurrent) || (guess === 'lower' && next < hiloCurrent);
            let res = document.getElementById('hiloResult');
            if(win) {{
                let winAmt = Math.floor(bet * 1.8);
                updateBalance(winAmt);
                res.innerHTML = `<span style="color:var(--accent-green);">📈 Угадали! +${{winAmt}}</span>`;
                triggerHaptic('success');
            }} else {{
                res.innerHTML = `<span style="color:var(--accent-red);">📉 Не угадали! Проигрыш</span>`;
                triggerHaptic('error');
            }}
            hiloCurrent = next;
        }}

        /* --- 10. КОЛЕСО ФОРТУНЫ --- */
        const wheelSectors = [0, 2, 1, 5, 0, 3, 10, 1];
        function drawFortuneWheel(angle) {{
            const canvas = document.getElementById('wheelCanvas');
            if(!canvas) return;
            const ctx = canvas.getContext('2d');
            const rad = canvas.width / 2;
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.save();
            ctx.translate(rad, rad);
            ctx.rotate(angle);

            const slice = (2 * Math.PI) / wheelSectors.length;
            for(let i=0; i<wheelSectors.length; i++) {{
                ctx.beginPath();
                ctx.moveTo(0,0);
                ctx.arc(0, 0, rad - 5, i * slice, (i + 1) * slice);
                ctx.fillStyle = wheelSectors[i] === 0 ? '#c0392b' : (i % 2 === 0 ? '#f39c12' : '#27ae60');
                ctx.fill();
                ctx.lineWidth = 1;
                ctx.strokeStyle = '#fff';
                ctx.stroke();

                ctx.save();
                ctx.rotate(i * slice + slice / 2);
                ctx.textAlign = "right";
                ctx.fillStyle = "#fff";
                ctx.font = "bold 12px Outfit";
                ctx.fillText("x" + wheelSectors[i], rad - 15, 4);
                ctx.restore();
            }}
            ctx.restore();

            ctx.fillStyle = "#fff";
            ctx.beginPath();
            ctx.moveTo(rad - 6, 0);
            ctx.lineTo(rad + 6, 0);
            ctx.lineTo(rad, 12);
            ctx.fill();
        }}

        function playWheel() {{
            let bet = parseInt(document.getElementById('wheelBet').value);
            if (bet > balance || bet <= 0) return alert('Недостаточно средств!');
            updateBalance(-bet); triggerHaptic('heavy');
            
            let targetIdx = Math.floor(Math.random() * wheelSectors.length);
            let slice = (2 * Math.PI) / wheelSectors.length;
            let finalAngle = Math.PI * 10 - (targetIdx * slice + slice / 2);
            
            let startTime = null;
            let duration = 3000;
            function animateWheel(timestamp) {{
                if(!startTime) startTime = timestamp;
                let progress = (timestamp - startTime) / duration;
                if(progress > 1) progress = 1;
                let ease = 1 - Math.pow(1 - progress, 3);
                drawFortuneWheel(finalAngle * ease);
                if(progress < 1) {{
                    requestAnimationFrame(animateWheel);
                }} else {{
                    let m = wheelSectors[targetIdx];
                    let res = document.getElementById('wheelResult');
                    if(m > 0) {{
                        let win = bet * m; updateBalance(win);
                        res.innerHTML = `<span style="color:var(--accent-gold);">🎯 Сектор x${{m}}! +${{win}}</span>`;
                        triggerHaptic('success');
                    }} else {{
                        res.innerHTML = `<span style="color:var(--accent-red);">🎯 Сектор НОЛЬ. Мимо</span>`;
                        triggerHaptic('error');
                    }}
                }}
            }}
            requestAnimationFrame(animateWheel);
        }}

        /* --- 11. КЕНО --- */
        function playKeno() {{
            let bet = parseInt(document.getElementById('kenoBet').value);
            if (bet > balance || bet <= 0) return alert('Недостаточно средств!');
            updateBalance(-bet); triggerHaptic('medium');
            let drawn = [];
            while(drawn.length < 3) {{ let n = Math.floor(Math.random()*10)+1; if(!drawn.includes(n)) drawn.push(n); }}
            document.getElementById('kenoDrawn').innerText = drawn.join(', ');
            let res = document.getElementById('kenoResult');
            if(drawn.includes(7)) {{
                let win = bet * 4; updateBalance(win);
                res.innerHTML = `<span style="color:var(--accent-green);">🔢 Совпало число 7! +${{win}}</span>`;
                triggerHaptic('success');
            }} else {{
                res.innerHTML = `<span style="color:var(--accent-red);">🔢 Тираж мимо</span>`;
                triggerHaptic('error');
            }}
        }}

        /* --- 12. СКРЕТЧ --- */
        let scratchItems = ['💎', '💎', '🍒', '🍋'];
        function startScratch() {{
            let bet = parseInt(document.getElementById('scratchBet').value);
            if (bet > balance || bet <= 0) return alert('Недостаточно средств!');
            updateBalance(-bet); triggerHaptic('light');
            scratchItems.sort(() => Math.random() - 0.5);
            for(let i=0; i<4; i++) {{
                let el = document.getElementById(`sc${{i}}`);
                el.innerText = '❓'; el.style.background = 'rgba(255,255,255,0.04)';
            }}
            document.getElementById('scratchResult').innerText = 'Сотрите билет';
        }}
        function revealScratch(idx) {{
            let el = document.getElementById(`sc${{idx}}`);
            if(el.innerText !== '❓') return;
            el.innerText = scratchItems[idx];
            el.style.background = 'rgba(39,174,96,0.25)';
            triggerHaptic('light');
            let revealedCount = Array.from(document.querySelectorAll('#scratchGrid > div')).filter(e => e.innerText !== '❓').length;
            if(revealedCount === 4) {{
                let countGems = scratchItems.filter(x => x === '💎').length;
                let bet = parseInt(document.getElementById('scratchBet').value);
                let res = document.getElementById('scratchResult');
                if(countGems >= 2) {{
                    let win = bet * 3; updateBalance(win);
                    res.innerHTML = `<span style="color:var(--accent-green);">🎫 Алмазы! +${{win}}</span>`;
                    triggerHaptic('success');
                }} else {{
                    res.innerHTML = `<span style="color:var(--accent-red);">🎫 Пусто</span>`;
                    triggerHaptic('error');
                }}
            }}
        }}
    </script>
</body>
</html>
"""

async def handle_webapp(request):
    return web.Response(text=WEBAPP_HTML, content_type="text/html")

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎰 Открыть Casino Royale", web_app=WebAppInfo(url=WEBAPP_URL))]
        ]
    )
    await message.answer("🎰 **Добро пожаловать в Grand Royale Casino!**", reply_markup=keyboard, parse_mode="Markdown")

@router.inline_query()
async def inline_handler(query: InlineQuery):
    articles = [
        InlineQueryResultArticle(
            id="casino_app",
            title="🎰 Casino Royale",
            description="Реальное мобильное казино",
            input_message_content=InputTextMessageContent(message_text="🎰 Я открыл казино! Присоединяйся."),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🎲 Играть", web_app=WebAppInfo(url=WEBAPP_URL))]])
        )
    ]
    await query.answer(articles, cache_time=1, is_personal=True)

async def main():
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

    print(f"Бот запущен на порту {port}!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
