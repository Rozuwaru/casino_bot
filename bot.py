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
TOKEN = "8752641180:AAEFfiJn6ykMK_ymFE4hc6kHKBOzgb9YWK8"

# ЗАМЕНИ НА СВОЙ URL С RENDER (например: https://my-casino-bot.onrender.com/webapp)
"WEBAPP_URL = "https://casino-bot-y2qo.onrender.com/webapp"

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

# --- ИНТЕРАКТИВНОЕ ОКНО КАЗИНО (MINI APP HTML/CSS/JS) ---
WEBAPP_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Grand Royale Casino</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0d0f17;
            --card-bg: #161926;
            --accent-gold: #ffb703;
            --accent-red: #e63946;
            --accent-green: #2a9d8f;
            --text-main: #ffffff;
            --text-dim: #8d99ae;
        }

        * {
            box-sizing: border-box;
            user-select: none;
            -webkit-user-select: none;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-main);
            font-family: 'Poppins', sans-serif;
            margin: 0;
            padding: 16px;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        /* HEADER & BALANCE */
        .header {
            width: 100%;
            max-width: 440px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: var(--card-bg);
            padding: 12px 20px;
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
            margin-bottom: 20px;
        }

        .logo {
            font-weight: 800;
            font-size: 18px;
            color: var(--accent-gold);
            text-transform: uppercase;
            letter-spacing: 1px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .balance-box {
            background: rgba(42, 157, 143, 0.15);
            border: 1px solid var(--accent-green);
            padding: 6px 14px;
            border-radius: 12px;
            font-weight: 600;
            color: #48cae4;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        /* CONTAINER */
        .container {
            width: 100%;
            max-width: 440px;
        }

        /* NAVIGATION BUTTONS */
        .back-btn {
            background: rgba(255, 255, 255, 0.08);
            color: var(--text-main);
            border: none;
            padding: 10px 16px;
            border-radius: 12px;
            font-weight: 600;
            cursor: pointer;
            margin-bottom: 16px;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            transition: 0.2s;
        }

        .back-btn:active { transform: scale(0.95); }

        /* GAMES LOBBY GRID */
        .lobby-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 14px;
        }

        .game-card {
            background: var(--card-bg);
            border-radius: 18px;
            padding: 20px 14px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.05);
            cursor: pointer;
            transition: all 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            position: relative;
            overflow: hidden;
        }

        .game-card:hover, .game-card:active {
            transform: translateY(-4px);
            border-color: var(--accent-gold);
            box-shadow: 0 8px 24px rgba(255, 183, 3, 0.2);
        }

        .game-icon {
            font-size: 38px;
            margin-bottom: 8px;
            display: block;
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

        /* GAME SCREEN WRAPPER */
        .game-screen {
            display: none;
            background: var(--card-bg);
            border-radius: 20px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            text-align: center;
        }

        .game-screen.active {
            display: block;
            animation: fadeIn 0.3s ease-in-out;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* INPUTS & BUTTONS */
        .bet-control {
            margin: 16px 0;
            display: flex;
            gap: 8px;
            justify-content: center;
            align-items: center;
        }

        .bet-input {
            width: 100px;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 10px;
            color: var(--accent-gold);
            font-weight: 700;
            font-size: 16px;
            text-align: center;
            padding: 8px;
        }

        .action-btn {
            background: linear-gradient(135deg, #ffb703, #fb8500);
            color: #000;
            border: none;
            width: 100%;
            padding: 14px;
            font-size: 16px;
            font-weight: 800;
            border-radius: 12px;
            cursor: pointer;
            transition: 0.2s;
            box-shadow: 0 4px 15px rgba(251, 133, 0, 0.3);
            text-transform: uppercase;
        }

        .action-btn:active { transform: scale(0.97); }

        .result-box {
            margin-top: 14px;
            font-weight: 600;
            min-height: 24px;
            font-size: 15px;
        }

        /* SLOTS ANIMATION */
        .slots-reels {
            display: flex;
            justify-content: center;
            gap: 10px;
            font-size: 42px;
            background: rgba(0,0,0,0.4);
            padding: 16px;
            border-radius: 14px;
            border: 2px solid var(--accent-gold);
            margin: 16px 0;
        }

        .reel {
            width: 60px;
            height: 60px;
            line-height: 60px;
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
        }

        /* MINES GRID */
        .mines-grid {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 6px;
            margin: 16px 0;
        }

        .mine-tile {
            aspect-ratio: 1;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            cursor: pointer;
            transition: 0.2s;
        }

        .mine-tile.revealed { background: rgba(255, 255, 255, 0.2); }
        .mine-tile.gem { background: rgba(42, 157, 143, 0.4); border: 1px solid var(--accent-green); }
        .mine-tile.bomb { background: rgba(230, 57, 70, 0.4); border: 1px solid var(--accent-red); }

        /* CRASH CANVAS */
        .crash-display {
            background: #000;
            height: 140px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 36px;
            font-weight: 800;
            color: var(--accent-gold);
            margin: 16px 0;
            border: 1px solid rgba(255,255,255,0.1);
        }

        /* BLACKJACK */
        .cards-area {
            display: flex;
            justify-content: space-around;
            margin: 14px 0;
            background: rgba(0,0,0,0.2);
            padding: 10px;
            border-radius: 12px;
        }
        .hand { font-size: 14px; }
        .hand-cards { font-size: 22px; font-weight: bold; margin-top: 4px; }

        /* ROULETTE & DICE */
        .flex-btns {
            display: flex;
            gap: 8px;
            margin-bottom: 12px;
        }
        .flex-btns button {
            flex: 1;
            padding: 10px;
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.1);
            color: #fff;
            border-radius: 10px;
            font-weight: 600;
            cursor: pointer;
        }
        .flex-btns button.selected {
            border-color: var(--accent-gold);
            background: rgba(255, 183, 3, 0.2);
        }
    </style>
</head>
<body>

    <div class="header">
        <div class="logo">🎰 Casino Royale</div>
        <div class="balance-box">🪙 <span id="userBalance">1000</span></div>
    </div>

    <div class="container">

        <!-- LOBBY -->
        <div id="lobby" class="lobby-grid">
            <div class="game-card" onclick="openGame('slots')">
                <span class="game-icon">🎰</span>
                <div class="game-title">Слоты 777</div>
                <div class="game-desc">Классический барабан</div>
            </div>
            <div class="game-card" onclick="openGame('roulette')">
                <span class="game-icon">🎡</span>
                <div class="game-title">Рулетка</div>
                <div class="game-desc">Красное, Черное, Зеро</div>
            </div>
            <div class="game-card" onclick="openGame('blackjack')">
                <span class="game-icon">🃏</span>
                <div class="game-title">Блэкджек</div>
                <div class="game-desc">Собери 21 очко</div>
            </div>
            <div class="game-card" onclick="openGame('mines')">
                <span class="game-icon">💣</span>
                <div class="game-title">Минное поле</div>
                <div class="game-desc">Ищи кристаллы</div>
            </div>
            <div class="game-card" onclick="openGame('crash')">
                <span class="game-icon">🚀</span>
                <div class="game-title">Краш X</div>
                <div class="game-desc">Забери до взрыва</div>
            </div>
            <div class="game-card" onclick="openGame('dice')">
                <span class="game-icon">🎲</span>
                <div class="game-title">Кости</div>
                <div class="game-desc">Больше или меньше</div>
            </div>
            <div class="game-card" onclick="openGame('coin')">
                <span class="game-icon">🪙</span>
                <div class="game-title">Монетка</div>
                <div class="game-desc">Орел или Решка</div>
            </div>
        </div>

        <!-- GAME: SLOTS -->
        <div id="game-slots" class="game-screen">
            <button class="back-btn" onclick="showLobby()">⬅ Назад в лобби</button>
            <h3>🎰 Слоты 777</h3>
            <div class="slots-reels">
                <div class="reel" id="r1">❓</div>
                <div class="reel" id="r2">❓</div>
                <div class="reel" id="r3">❓</div>
            </div>
            <div class="bet-control">
                <label>Ставка:</label>
                <input type="number" id="slotsBet" class="bet-input" value="100" min="10">
            </div>
            <button class="action-btn" onclick="playSlots()">Крутить!</button>
            <div class="result-box" id="slotsResult"></div>
        </div>

        <!-- GAME: ROULETTE -->
        <div id="game-roulette" class="game-screen">
            <button class="back-btn" onclick="showLobby()">⬅ Назад в лобби</button>
            <h3>🎡 Рулетка</h3>
            <div class="flex-btns">
                <button id="roul-red" onclick="selectRoulette('red')" class="selected">🔴 Красное (x2)</button>
                <button id="roul-black" onclick="selectRoulette('black')">⚫ Черное (x2)</button>
                <button id="roul-zero" onclick="selectRoulette('zero')">🟢 Зеро (x14)</button>
            </div>
            <div class="bet-control">
                <label>Ставка:</label>
                <input type="number" id="rouletteBet" class="bet-input" value="100" min="10">
            </div>
            <button class="action-btn" onclick="playRoulette()">Вращать колесо</button>
            <div class="result-box" id="rouletteResult"></div>
        </div>

        <!-- GAME: BLACKJACK -->
        <div id="game-blackjack" class="game-screen">
            <button class="back-btn" onclick="showLobby()">⬅ Назад в лобби</button>
            <h3>🃏 Блэкджек 21</h3>
            <div class="cards-area">
                <div class="hand">
                    <div>Дилер: <span id="bjDealerScore">0</span></div>
                    <div class="hand-cards" id="bjDealerCards">🂠 🂠</div>
                </div>
                <div class="hand">
                    <div>Вы: <span id="bjPlayerScore">0</span></div>
                    <div class="hand-cards" id="bjPlayerCards">❓ ❓</div>
                </div>
            </div>
            <div class="bet-control">
                <label>Ставка:</label>
                <input type="number" id="bjBet" class="bet-input" value="100" min="10">
            </div>
            <div class="flex-btns" id="bjControls" style="display:none;">
                <button onclick="bjHit()" style="background:#2a9d8f;">Взять еще</button>
                <button onclick="bjStand()" style="background:#e63946;">Хватит</button>
            </div>
            <button class="action-btn" id="bjStartBtn" onclick="startBlackjack()">Раздать карты</button>
            <div class="result-box" id="bjResult"></div>
        </div>

        <!-- GAME: MINES -->
        <div id="game-mines" class="game-screen">
            <button class="back-btn" onclick="showLobby()">⬅ Назад в лобби</button>
            <h3>💣 Минное поле</h3>
            <div class="mines-grid" id="minesGrid"></div>
            <div class="bet-control">
                <label>Ставка:</label>
                <input type="number" id="minesBet" class="bet-input" value="100" min="10">
            </div>
            <button class="action-btn" id="minesStartBtn" onclick="startMines()">Начать игру</button>
            <button class="action-btn" id="minesCashoutBtn" onclick="cashoutMines()" style="display:none; background:#2a9d8f; margin-top:8px;">Забрать профит</button>
            <div class="result-box" id="minesResult"></div>
        </div>

        <!-- GAME: CRASH -->
        <div id="game-crash" class="game-screen">
            <button class="back-btn" onclick="showLobby()">⬅ Назад в лобби</button>
            <h3>🚀 Краш X</h3>
            <div class="crash-display" id="crashDisplay">1.00x</div>
            <div class="bet-control">
                <label>Ставка:</label>
                <input type="number" id="crashBet" class="bet-input" value="100" min="10">
            </div>
            <button class="action-btn" id="crashBtn" onclick="startCrash()">Старт</button>
            <div class="result-box" id="crashResult"></div>
        </div>

        <!-- GAME: DICE -->
        <div id="game-dice" class="game-screen">
            <button class="back-btn" onclick="showLobby()">⬅ Назад в лобби</button>
            <h3>🎲 Кости</h3>
            <div class="flex-btns">
                <button id="dice-low" onclick="selectDice('low')" class="selected">Меньше 4 (x2)</button>
                <button id="dice-high" onclick="selectDice('high')">Больше 3 (x2)</button>
            </div>
            <div class="bet-control">
                <label>Ставка:</label>
                <input type="number" id="diceBet" class="bet-input" value="100" min="10">
            </div>
            <button class="action-btn" onclick="playDice()">Бросить кость</button>
            <div class="result-box" id="diceResult"></div>
        </div>

        <!-- GAME: COIN -->
        <div id="game-coin" class="game-screen">
            <button class="back-btn" onclick="showLobby()">⬅ Назад в лобби</button>
            <h3>🪙 Монетка</h3>
            <div class="flex-btns">
                <button id="coin-heads" onclick="selectCoin('heads')" class="selected">🦅 Орел</button>
                <button id="coin-tails" onclick="selectCoin('tails')">🪙 Решка</button>
            </div>
            <div class="bet-control">
                <label>Ставка:</label>
                <input type="number" id="coinBet" class="bet-input" value="100" min="10">
            </div>
            <button class="action-btn" onclick="playCoin()">Подкинуть</button>
            <div class="result-box" id="coinResult"></div>
        </div>

    </div>

    <script>
        let tg = window.Telegram.WebApp;
        tg.expand();

        let balance = 1000;
        function updateBalance(amount) {
            balance += amount;
            document.getElementById('userBalance').innerText = balance;
        }

        function triggerHaptic(type = 'impact') {
            if (tg.HapticFeedback) {
                if (type === 'success') tg.HapticFeedback.notificationOccurred('success');
                else if (type === 'error') tg.HapticFeedback.notificationOccurred('error');
                else tg.HapticFeedback.impactOccurred('medium');
            }
        }

        function showLobby() {
            document.querySelectorAll('.game-screen').forEach(el => el.classList.remove('active'));
            document.getElementById('lobby').style.display = 'grid';
        }

        function openGame(gameId) {
            triggerHaptic();
            document.getElementById('lobby').style.display = 'none';
            document.getElementById(`game-${gameId}`).classList.add('active');
        }

        /* --- SLOTS --- */
        function playSlots() {
            let bet = parseInt(document.getElementById('slotsBet').value);
            if (bet > balance || bet <= 0) return alert('Недостаточно средств!');
            updateBalance(-bet);
            triggerHaptic();

            let items = ['🍒', '🍋', '🔔', '💎', '7️⃣'];
            let r1 = document.getElementById('r1');
            let r2 = document.getElementById('r2');
            let r3 = document.getElementById('r3');

            let timer = setInterval(() => {
                r1.innerText = items[Math.floor(Math.random() * items.length)];
                r2.innerText = items[Math.floor(Math.random() * items.length)];
                r3.innerText = items[Math.floor(Math.random() * items.length)];
            }, 80);

            setTimeout(() => {
                clearInterval(timer);
                let res1 = items[Math.floor(Math.random() * items.length)];
                let res2 = items[Math.floor(Math.random() * items.length)];
                let res3 = items[Math.floor(Math.random() * items.length)];
                r1.innerText = res1; r2.innerText = res2; r3.innerText = res3;

                let resBox = document.getElementById('slotsResult');
                if (res1 === res2 && res2 === res3) {
                    let win = bet * 5;
                    updateBalance(win);
                    resBox.innerText = `🎉 ДЖЕКПОТ! Выигрыш +${win}`;
                    triggerHaptic('success');
                } else if (res1 === res2 || res2 === res3 || res1 === res3) {
                    let win = Math.floor(bet * 1.5);
                    updateBalance(win);
                    resBox.innerText = `✨ Пара! Выигрыш +${win}`;
                    triggerHaptic('success');
                } else {
                    resBox.innerText = '😢 Не повезло!';
                    triggerHaptic('error');
                }
            }, 1000);
        }

        /* --- ROULETTE --- */
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
            triggerHaptic();

            let num = Math.floor(Math.random() * 37);
            let color = num === 0 ? 'zero' : (num % 2 === 0 ? 'black' : 'red');

            let resBox = document.getElementById('rouletteResult');
            if (color === selectedRoulette) {
                let mult = selectedRoulette === 'zero' ? 14 : 2;
                let win = bet * mult;
                updateBalance(win);
                resBox.innerText = ` Выпало ${num} (${color.toUpperCase()})! Выигрыш +${win}`;
                triggerHaptic('success');
            } else {
                resBox.innerText = ` Выпало ${num} (${color.toUpperCase()}). Мимо!`;
                triggerHaptic('error');
            }
        }

        /* --- BLACKJACK --- */
        let bjState = { player: [], dealer: [], playing: false };
        function getCard() { return Math.min(10, Math.floor(Math.random() * 10) + 1); }
        function sumHand(h) { return h.reduce((a,b)=>a+b, 0); }

        function startBlackjack() {
            let bet = parseInt(document.getElementById('bjBet').value);
            if (bet > balance || bet <= 0) return alert('Недостаточно средств!');
            updateBalance(-bet);
            triggerHaptic();

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
            bjState.player.push(getCard());
            renderBJ();
            if (sumHand(bjState.player) > 21) endBJ(false, 'Перебор!');
        }

        function bjStand() {
            if (!bjState.playing) return;
            while(sumHand(bjState.dealer) < 17) bjState.dealer.push(getCard());
            let p = sumHand(bjState.player), d = sumHand(bjState.dealer);
            if (d > 21 || p > d) endBJ(true, 'Победа!');
            else if (p === d) endBJ('draw', 'Ничья!');
            else endBJ(false, 'Дилер выиграл!');
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

        /* --- MINES --- */
        let minesState = { active: false, bombs: [], opened: 0, mult: 1.2 };
        function startMines() {
            let bet = parseInt(document.getElementById('minesBet').value);
            if (bet > balance || bet <= 0) return alert('Недостаточно средств!');
            updateBalance(-bet);
            triggerHaptic();

            let grid = document.getElementById('minesGrid');
            grid.innerHTML = '';
            let bombs = [];
            while(bombs.length < 3) {
                let r = Math.floor(Math.random()*25);
                if(!bombs.includes(r)) bombs.push(r);
            }
            minesState = { active: true, bombs: bombs, opened: 0, mult: 1.2, bet: bet };

            for(let i=0; i<25; i++) {
                let tile = document.createElement('div');
                tile.className = 'mine-tile';
                tile.onclick = () => clickMine(i, tile);
                grid.appendChild(tile);
            }
            document.getElementById('minesStartBtn').style.display = 'none';
            document.getElementById('minesCashoutBtn').style.display = 'block';
            document.getElementById('minesResult').innerText = 'Ищите кристаллы!';
        }

        function clickMine(idx, tile) {
            if(!minesState.active || tile.classList.contains('revealed')) return;
            tile.classList.add('revealed');
            if(minesState.bombs.includes(idx)) {
                tile.classList.add('bomb'); tile.innerText = '💣';
                minesState.active = false;
                document.getElementById('minesResult').innerText = '💥 БУМ! Вы подорвались!';
                document.getElementById('minesStartBtn').style.display = 'block';
                document.getElementById('minesCashoutBtn').style.display = 'none';
                triggerHaptic('error');
            } else {
                tile.classList.add('gem'); tile.innerText = '💎';
                minesState.opened++;
                minesState.mult += 0.3;
                let currentWin = Math.floor(minesState.bet * minesState.mult);
                document.getElementById('minesResult').innerText = `Профит: ${currentWin} (x${minesState.mult.toFixed(2)})`;
                triggerHaptic();
            }
        }

        function cashoutMines() {
            if(!minesState.active || minesState.opened === 0) return;
            let win = Math.floor(minesState.bet * minesState.mult);
            updateBalance(win);
            minesState.active = false;
            document.getElementById('minesResult').innerText = `💰 Забрал +${win} монет!`;
            document.getElementById('minesStartBtn').style.display = 'block';
            document.getElementById('minesCashoutBtn').style.display = 'none';
            triggerHaptic('success');
        }

        /* --- CRASH --- */
        let crashInterval = null;
        function startCrash() {
            let bet = parseInt(document.getElementById('crashBet').value);
            if (bet > balance || bet <= 0) return alert('Недостаточно средств!');
            updateBalance(-bet);
            triggerHaptic();

            let mult = 1.00;
            let crashPoint = (Math.random() * 4 + 1).toFixed(2);
            let btn = document.getElementById('crashBtn');
            let display = document.getElementById('crashDisplay');
            let active = true;

            btn.innerText = 'Забрать';
            btn.onclick = () => {
                if(!active) return;
                active = false;
                clearInterval(crashInterval);
                let win = Math.floor(bet * mult);
                updateBalance(win);
                document.getElementById('crashResult').innerText = ` Успел! Выиграл +${win}`;
                btn.innerText = 'Старт';
                btn.onclick = startCrash;
                triggerHaptic('success');
            };

            crashInterval = setInterval(() => {
                mult += 0.05;
                display.innerText = mult.toFixed(2) + 'x';
                if(mult >= crashPoint && active) {
                    active = false;
                    clearInterval(crashInterval);
                    display.innerText = '💥 CRASH!';
                    document.getElementById('crashResult').innerText = `Увы, улетел на ${crashPoint}x`;
                    btn.innerText = 'Старт';
                    btn.onclick = startCrash;
                    triggerHaptic('error');
                }
            }, 100);
        }

        /* --- DICE --- */
        let selectedDice = 'low';
        function selectDice(val) {
            selectedDice = val;
            document.querySelectorAll('#game-dice .flex-btns button').forEach(b => b.classList.remove('selected'));
            document.getElementById(`dice-${val}`).classList.add('selected');
        }
        function playDice() {
            let bet = parseInt(document.getElementById('diceBet').value);
            if (bet > balance || bet <= 0) return alert('Недостаточно средств!');
            updateBalance(-bet);
            triggerHaptic();

            let roll = Math.floor(Math.random()*6)+1;
            let win = (selectedDice === 'low' && roll <= 3) || (selectedDice === 'high' && roll >= 4);
            let res = document.getElementById('diceResult');
            if(win) {
                updateBalance(bet * 2);
                res.innerText = `🎲 Выпало ${roll}! Выигрыш +${bet*2}`;
                triggerHaptic('success');
            } else {
                res.innerText = `🎲 Выпало ${roll}! Проигрыш`;
                triggerHaptic('error');
            }
        }

        /* --- COIN --- */
        let selectedCoin = 'heads';
        function selectCoin(val) {
            selectedCoin = val;
            document.querySelectorAll('#game-coin .flex-btns button').forEach(b => b.classList.remove('selected'));
            document.getElementById(`coin-${val}`).classList.add('selected');
        }
        function playCoin() {
            let bet = parseInt(document.getElementById('coinBet').value);
            if (bet > balance || bet <= 0) return alert('Недостаточно средств!');
            updateBalance(-bet);
            triggerHaptic();

            let resVal = Math.random() < 0.5 ? 'heads' : 'tails';
            let res = document.getElementById('coinResult');
            if(resVal === selectedCoin) {
                updateBalance(bet * 2);
                res.innerText = ` Выпало: ${resVal === 'heads' ? 'ОРЕЛ' : 'РЕШКА'}! Выигрыш +${bet*2}`;
                triggerHaptic('success');
            } else {
                res.innerText = ` Выпало: ${resVal === 'heads' ? 'ОРЕЛ' : 'РЕШКА'}! Проиграл`;
                triggerHaptic('error');
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
            [InlineKeyboardButton(text="🎰 Играть в Casino Royale", web_app=WebAppInfo(url=WEBAPP_URL))]
        ]
    )
    await message.answer(
        "🎰 **Добро пожаловать в Grand Royale Casino!**\n\n"
        "Теперь ты можешь запускать казино в **абсолютно любом чате** без добавления бота!\n\n"
        "Просто напиши в строке ввода любого чата имя бота (например, `@casino_p0tat0777_bot`) и нажми на всплывающую карточку!",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@router.inline_query()
async def inline_handler(query: InlineQuery):
    add_user(query.from_user.id)
    articles = [
        InlineQueryResultArticle(
            id="casino_app",
            title="🎰 Casino Royale (Игровой Зал)",
            description="Слоты, Рулетка, Минное поле, Краш, Блэкджек и Кости в одном окне",
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
