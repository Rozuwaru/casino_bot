import asyncio
import logging
import os
import json
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

# Конфигурационные параметры бота и базы данных
TOKEN = "8752641180:AAET94FACuNdO26CCdFHFyv1vJhSiv3O7F4"
WEBAPP_URL = "https://casino-bot-y2qo.onrender.com/webapp"

SUPABASE_URL = "https://lnskcqunuaewqcsvcpvr.supabase.co"
SUPABASE_KEY = "yJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imxuc2tjcXVudWFld3Fjc3ZjcHZyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTMwMzE2MjQsImV4cCI6MjEwODYwNzYyNH0.g0F_E6hIOeholtABi_WsbMzqT4H-49wTH5XYXAk_0Nc"

# Тяжеловесный HTML/CSS/JS интерфейс казино
WEBAPP_HTML = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no, maximum-scale=1.0">
    <title>SpadeKing Elite Casino & Sports</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-main: #0c0f1d;
            --bg-sidebar: #070914;
            --panel-bg: #11162a;
            --panel-hover: #19203d;
            --gold-grad: linear-gradient(135deg, #ffe066 0%, #f39c12 50%, #d35400 100%);
            --accent-gold: #f39c12;
            --accent-green: #2ecc71;
            --accent-red: #e74c3c;
            --text-main: #ffffff;
            --text-dim: #8a98a8;
            --border: rgba(255, 255, 255, 0.08);
        }}
        * {{ box-sizing: border-box; user-select: none; -webkit-user-select: none; margin: 0; padding: 0; font-family: 'Montserrat', sans-serif; }}
        body {{ background-color: var(--bg-main); color: var(--text-main); min-height: 100vh; display: flex; overflow-x: hidden; }}

        /* СТИЛИ БОКОВОЙ ПАНЕЛИ */
        .sidebar {{
            width: 250px; background: var(--bg-sidebar); border-right: 1px solid var(--border);
            display: flex; flex-direction: column; position: fixed; height: 100vh; z-index: 300; transition: 0.3s;
        }}
        .sidebar-brand {{ padding: 22px; font-weight: 900; font-size: 19px; display: flex; align-items: center; gap: 10px; background: var(--gold-grad); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .sidebar-menu {{ display: flex; flex-direction: column; gap: 6px; padding: 10px; overflow-y: auto; flex: 1; }}
        .menu-category-title {{ font-size: 10px; text-transform: uppercase; color: var(--text-dim); font-weight: 800; padding: 10px 16px 4px; letter-spacing: 1px; }}
        .menu-item {{
            display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-radius: 12px; color: var(--text-dim);
            font-weight: 600; font-size: 14px; cursor: pointer; transition: 0.2s; text-decoration: none;
        }}
        .menu-item:hover, .menu-item.active {{ background: var(--panel-hover); color: var(--text-main); }}
        .menu-item span {{ font-size: 18px; }}

        /* ОСНОВНОЙ МАКЕТ */
        .main-wrapper {{ flex: 1; margin-left: 250px; display: flex; flex-direction: column; min-height: 100vh; }}

        /* ВЕРХНЯЯ ШАПКА ПРОФИЛЯ И НАВИГАЦИИ */
        .header {{
            height: 75px; background: var(--panel-bg); border-bottom: 1px solid var(--border);
            display: flex; justify-content: space-between; align-items: center; padding: 0 28px;
            position: sticky; top: 0; z-index: 200; backdrop-filter: blur(12px);
        }}
        .header-left {{ display: flex; gap: 15px; align-items: center; }}
        .tab-btn {{ background: transparent; border: none; color: var(--text-dim); font-weight: 700; font-size: 14px; cursor: pointer; padding: 8px 16px; border-radius: 10px; transition: 0.2s; }}
        .tab-btn.active {{ background: var(--accent-gold); color: #000; box-shadow: 0 4px 15px rgba(243,156,18,0.3); }}
        
        .header-right {{ display: flex; align-items: center; gap: 16px; }}
        .user-profile {{ display: flex; align-items: center; gap: 10px; background: rgba(255,255,255,0.04); padding: 6px 16px; border-radius: 30px; border: 1px solid var(--border); }}
        .user-avatar {{ width: 34px; height: 34px; border-radius: 50%; background: #f39c12; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 15px; }}
        .user-balance {{ font-weight: 800; color: var(--accent-green); font-size: 14px; }}
        .icon-btn {{ width: 40px; height: 40px; border-radius: 50%; background: var(--panel-hover); border: 1px solid var(--border); display: flex; align-items: center; justify-content: center; cursor: pointer; color: #fff; transition: 0.2s; }}
        .icon-btn:hover {{ border-color: var(--accent-gold); }}

        /* КОНТЕНТНАЯ ЗОНА */
        .content-area {{ padding: 28px; flex: 1; display: flex; flex-direction: column; gap: 28px; }}

        .view-section {{ display: none; }}
        .view-section.active {{ display: flex; flex-direction: column; gap: 28px; animation: fadeIn 0.35s ease; }}
        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: translateY(0); }} }}

        /* БАННЕР СОБЫТИЯ «CHAT RAIN» И ТАЙМЕРЫ */
        .promo-banner {{
            display: grid; grid-template-columns: 2fr 1fr; gap: 24px;
            background: linear-gradient(135deg, #182042 0%, #0d1224 100%);
            border-radius: 22px; padding: 28px; border: 1px solid var(--border); position: relative; overflow: hidden;
            box-shadow: 0 15px 35px rgba(0,0,0,0.5);
        }}
        .countdown-boxes {{ display: flex; gap: 12px; margin-top: 16px; }}
        .c-box {{ background: var(--accent-gold); color: #000; width: 50px; height: 56px; border-radius: 12px; display: flex; flex-direction: column; align-items: center; justify-content: center; font-weight: 900; font-size: 20px; box-shadow: 0 6px 20px rgba(243,156,18,0.4); }}
        .c-box span {{ font-size: 9px; font-weight: 700; text-transform: uppercase; }}

        /* СЕТКА ИГР В ЛОББИ */
        .games-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 18px; }}
        .game-tile {{
            background: var(--panel-bg); border-radius: 18px; padding: 22px; border: 1px solid var(--border);
            cursor: pointer; transition: 0.3s; display: flex; flex-direction: column; align-items: center; text-align: center;
            box-shadow: 0 10px 25px rgba(0,0,0,0.3); position: relative; overflow: hidden;
        }}
        .game-tile:hover {{ transform: translateY(-6px); border-color: var(--accent-gold); box-shadow: 0 15px 35px rgba(243, 156, 18, 0.3); }}
        .tile-icon {{ font-size: 52px; margin-bottom: 14px; filter: drop-shadow(0 5px 10px rgba(0,0,0,0.5)); }}
        .tile-title {{ font-size: 17px; font-weight: 800; margin-bottom: 6px; }}
        .tile-sub {{ font-size: 12px; color: var(--text-dim); }}

        /* ПОБЕДИТЕЛИ */
        .live-winners {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }}
        .winner-card {{ background: var(--panel-bg); border-radius: 16px; padding: 16px; border: 1px solid var(--border); display: flex; align-items: center; gap: 14px; box-shadow: 0 8px 20px rgba(0,0,0,0.3); }}
        .winner-avatar {{ width: 44px; height: 44px; border-radius: 50%; background: #1a223d; display: flex; align-items: center; justify-content: center; font-size: 20px; }}

        /* ИГРОВЫЕ МОДУЛИ */
        .game-container {{ background: var(--panel-bg); border-radius: 22px; padding: 28px; border: 1px solid var(--border); display: flex; flex-direction: column; align-items: center; gap: 22px; max-width: 680px; margin: 0 auto; width: 100%; box-shadow: 0 20px 50px rgba(0,0,0,0.7); }}
        .bet-panel {{ display: flex; gap: 14px; width: 100%; align-items: center; background: #080a14; padding: 14px 20px; border-radius: 16px; border: 1px solid var(--border); }}
        .bet-input {{ background: transparent; border: none; color: var(--accent-gold); font-size: 20px; font-weight: 900; width: 110px; outline: none; text-align: center; }}
        .play-btn {{ flex: 1; background: var(--gold-grad); color: #000; border: none; padding: 16px; border-radius: 14px; font-weight: 900; font-size: 16px; cursor: pointer; text-transform: uppercase; box-shadow: 0 8px 25px rgba(243,156,18,0.4); transition: 0.2s; }}
        .play-btn:active {{ transform: scale(0.98); }}

        /* РУЛЕТКА */
        .roulette-table-wrap {{ background: #0b532c; border: 6px solid #06361c; border-radius: 18px; padding: 18px; width: 100%; box-shadow: inset 0 0 35px rgba(0,0,0,0.9); }}
        .r-grid {{ display: grid; grid-template-columns: 50px repeat(12, 1fr); gap: 4px; font-weight: 800; font-size: 13px; text-align: center; color: #fff; }}
        .rc {{ background: #13773f; border: 1px solid rgba(255,255,255,0.3); padding: 14px 0; border-radius: 6px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: 0.2s; }}
        .rc:hover {{ filter: brightness(1.2); }}
        .rc.red {{ background: #c0392b; }}
        .rc.black {{ background: #111; }}
        .rc.zero {{ grid-row: span 3; background: #27ae60; font-size: 18px; }}

        /* СЛОТЫ */
        .slots-box {{ background: linear-gradient(180deg, #f1c40f 0%, #d35400 100%); padding: 12px; border-radius: 22px; box-shadow: 0 0 35px rgba(241,196,15,0.4); width: 100%; }}
        .slots-inner {{ background: #050714; border-radius: 16px; display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; padding: 12px; }}
        .slot-reel {{ background: linear-gradient(180deg, #13192f 0%, #0c1020 100%); height: 90px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 42px; border: 1px solid var(--border); }}

        /* МИНЫ */
        .mines-box {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; width: 100%; max-width: 420px; }}
        .mine-tile {{ aspect-ratio: 1; background: #1a223d; border-radius: 14px; border: 1px solid var(--border); display: flex; align-items: center; justify-content: center; font-size: 28px; cursor: pointer; transition: 0.2s; box-shadow: inset 0 -4px 0 rgba(0,0,0,0.5); }}
        .mine-tile:active {{ transform: scale(0.95); }}

        @media(max-width: 768px) {{
            .sidebar {{ display: none; }}
            .main-wrapper {{ margin-left: 0; }}
            .live-winners {{ grid-template-columns: repeat(2, 1fr); }}
            .promo-banner {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>

    <!-- БОКОВАЯ ПАНЕЛЬ НАВИГАЦИИ СПАДКИНГ -->
    <div class="sidebar">
        <div class="sidebar-brand">👑 SPADE KING</div>
        <div class="sidebar-menu">
            <div class="menu-category-title">Главное</div>
            <a class="menu-item active" onclick="switchTab('lobby')"><span>🏠</span> Lobby</a>
            <a class="menu-item" onclick="openGame('roulette')"><span>🎡</span> Roulette Table</a>
            <a class="menu-item" onclick="openGame('slots')"><span>🎰</span> Slots 5x3</a>
            <a class="menu-item" onclick="openGame('crash')"><span>🚀</span> Crash Space</a>
            <a class="menu-item" onclick="openGame('mines')"><span>💣</span> Sapphire Mines</a>
            <a class="menu-item" onclick="openGame('plinko')"><span>🔺</span> Plinko Pyramid</a>
            <div class="menu-category-title">Разделы</div>
            <a class="menu-item" onclick="alert('Live Casino streams available soon')"><span>🎥</span> Live Casino</a>
            <a class="menu-item" onclick="alert('Sportsbook section')"><span>⚽</span> Sports Betting</a>
            <a class="menu-item" onclick="alert('VIP Bonus system')"><span>🎁</span> Bonuses</a>
        </div>
    </div>

    <div class="main-wrapper">
        <!-- ВЕРХНЯЯ ШАПКА -->
        <div class="header">
            <div class="header-left">
                <button class="tab-btn active" onclick="switchTab('lobby')">Casino</button>
                <button class="tab-btn" onclick="alert('Sports section is launching!')">Sports</button>
            </div>
            <div class="header-right">
                <div class="user-profile">
                    <div class="user-avatar">👑</div>
                    <div class="user-balance">🪙 <span id="userBalance">1000.00</span></div>
                </div>
                <div class="icon-btn" onclick="alert('Настройки профиля и безопасности')">⚙️</div>
                <div class="icon-btn" onclick="alert('У вас нет новых уведомлений')">🔔</div>
            </div>
        </div>

        <div class="content-area">

            <!-- РАЗДЕЛ ЛОББИ -->
            <div id="view-lobby" class="view-section active">
                
                <!-- БАННЕР CHAT RAIN -->
                <div class="promo-banner">
                    <div>
                        <h2 style="font-size: 24px; font-weight: 900; margin-bottom: 8px;">Chat Rain Event 🌧️</h2>
                        <p style="color: var(--text-dim); font-size: 13px; margin-bottom: 16px;">Randomly reward active player chat rooms every 5 hours. Get ready for massive crypto distributions!</p>
                        <div class="countdown-boxes">
                            <div class="c-box"><div id="cd-d">07</div><span>Days</span></div>
                            <div class="c-box"><div id="cd-h">08</div><span>Hours</span></div>
                            <div class="c-box"><div id="cd-m">05</div><span>Mins</span></div>
                            <div class="c-box"><div id="cd-s">04</div><span>Secs</span></div>
                        </div>
                    </div>
                    <div style="display: flex; flex-direction: column; justify-content: center; gap: 12px;">
                        <button class="play-btn" style="padding: 12px 20px; font-size: 14px;" onclick="alert('Вы успешно присоединились к Chat Rain!')">💬 Join Chat Room</button>
                        <button class="tab-btn" style="background: rgba(255,255,255,0.06); color:#fff;" onclick="alert('Список друзей пуст')">👥 Friends List</button>
                    </div>
                </div>

                <h3 style="font-size: 20px; font-weight: 800;">Featured Casino Games</h3>
                <div class="games-grid">
                    <div class="game-tile" onclick="openGame('roulette')">
                        <span class="tile-icon">🎡</span>
                        <div class="tile-title">European Roulette</div>
                        <div class="tile-sub">Classic table gameplay</div>
                    </div>
                    <div class="game-tile" onclick="openGame('slots')">
                        <span class="tile-icon">🎰</span>
                        <div class="tile-title">VIP Slots 5x3</div>
                        <div class="tile-sub">High multiplier reels</div>
                    </div>
                    <div class="game-tile" onclick="openGame('crash')">
                        <span class="tile-icon">🚀</span>
                        <div class="tile-title">Crash Space</div>
                        <div class="tile-sub">Aviator rocket flight</div>
                    </div>
                    <div class="game-tile" onclick="openGame('mines')">
                        <span class="tile-icon">💣</span>
                        <div class="tile-title">Sapphire Mines</div>
                        <div class="tile-sub">Grid 5x5 hazard test</div>
                    </div>
                    <div class="game-tile" onclick="openGame('plinko')">
                        <span class="tile-icon">🔺</span>
                        <div class="tile-title">Plinko Pyramid</div>
                        <div class="tile-sub">Risk drops & pegs</div>
                    </div>
                </div>

                <h3 style="font-size: 20px; font-weight: 800; margin-top: 10px;">Top Live Winners</h3>
                <div class="live-winners">
                    <div class="winner-card"><div class="winner-avatar">👑</div><div><div style="font-weight:700; font-size:14px;">Imran</div><div style="color:var(--accent-green); font-size:12px;">+2,450.00 🪙</div></div></div>
                    <div class="winner-card"><div class="winner-avatar">⚡</div><div><div style="font-weight:700; font-size:14px;">Murad</div><div style="color:var(--accent-green); font-size:12px;">+1,120.00 🪙</div></div></div>
                    <div class="winner-card"><div class="winner-avatar">💎</div><div><div style="font-weight:700; font-size:14px;">Raihgd</div><div style="color:var(--accent-green); font-size:12px;">+980.00 🪙</div></div></div>
                    <div class="winner-card"><div class="winner-avatar">🔥</div><div><div style="font-weight:700; font-size:14px;">Yousuf</div><div style="color:var(--accent-green); font-size:12px;">+5,400.00 🪙</div></div></div>
                </div>

            </div>

            <!-- ИГРОВЫЕ МОДУЛИ -->
            
            <!-- 1. ЕВРОПЕЙСКАЯ РУЛЕТКА -->
            <div id="view-roulette" class="view-section">
                <div class="game-container">
                    <h3 style="font-weight: 900; font-size: 22px;">🎡 European Roulette Table</h3>
                    <div style="text-align:center;"><canvas id="roulCanvas" width="180" height="180" style="border-radius:50%; border:4px solid var(--accent-gold); box-shadow: 0 0 25px rgba(243,156,18,0.4);"></canvas></div>
                    <div class="roulette-table-wrap">
                        <div class="r-grid">
                            <div class="rc zero" onclick="setRoulBet('0')">0</div>
                            <div class="rc red" onclick="setRoulBet('3')">3</div><div class="rc black" onclick="setRoulBet('6')">6</div><div class="rc red" onclick="setRoulBet('9')">9</div>
                            <div class="rc red" onclick="setRoulBet('12')">12</div><div class="rc black" onclick="setRoulBet('15')">15</div><div class="rc red" onclick="setRoulBet('18')">18</div>
                            <div class="rc red" onclick="setRoulBet('21')">21</div><div class="rc black" onclick="setRoulBet('24')">24</div><div class="rc red" onclick="setRoulBet('27')">27</div>
                            <div class="rc red" onclick="setRoulBet('30')">30</div><div class="rc black" onclick="setRoulBet('33')">33</div><div class="rc red" onclick="setRoulBet('36')">36</div>
                        </div>
                    </div>
                    <div style="display:flex; gap:10px; width:100%;">
                        <button class="play-btn" style="background:#c0392b; color:#fff;" onclick="setRoulBet('red')">RED (x2)</button>
                        <button class="play-btn" style="background:#111; color:#fff;" onclick="setRoulBet('black')">BLACK (x2)</button>
                    </div>
                    <div class="bet-panel">
                        <span>Ставка:</span>
                        <input type="number" id="roulBet" class="bet-input" value="10">
                        <button class="play-btn" onclick="spinRouletteTable()">SPIN</button>
                    </div>
                    <div id="roulResult" style="font-weight:800; font-size:16px;">Ставка на: <span id="roulChoice" style="color:var(--accent-gold);">RED</span></div>
                </div>
            </div>

            <!-- 2. СЛОТЫ 5x3 -->
            <div id="view-slots" class="view-section">
                <div class="game-container">
                    <h3 style="font-weight: 900; font-size: 22px;">🎰 5x3 VIP Slot Machine</h3>
                    <div class="slots-box">
                        <div class="slots-inner" id="slotsScreen"></div>
                    </div>
                    <div class="bet-panel">
                        <span>Ставка:</span>
                        <input type="number" id="slotsBet" class="bet-input" value="10">
                        <button class="play-btn" onclick="spinSlots5x3()">SPIN REELS</button>
                    </div>
                    <div id="slotsResult" style="font-weight:800; font-size:16px;"></div>
                </div>
            </div>

            <!-- 3. КРАШ КОСМОС -->
            <div id="view-crash" class="view-section">
                <div class="game-container">
                    <h3 style="font-weight: 900; font-size: 22px;">🚀 Crash Space Flight</h3>
                    <div style="width:100%; height:250px; background:#030511; border-radius:16px; position:relative; overflow:hidden; border:1px solid var(--border); display:flex; align-items:center; justify-content:center; box-shadow: inset 0 0 40px rgba(0,0,0,0.8);">
                        <div id="crashMultiplier" style="font-size:56px; font-weight:900; color:#fff; text-shadow:0 0 25px rgba(243,156,18,0.6);">1.00x</div>
                    </div>
                    <div class="bet-panel">
                        <span>Ставка:</span>
                        <input type="number" id="crashBet" class="bet-input" value="10">
                        <button class="play-btn" id="crashActionBtn" onclick="toggleCrash()">LAUNCH ROCKET</button>
                    </div>
                    <div id="crashResult" style="font-weight:800; font-size:16px;"></div>
                </div>
            </div>

            <!-- 4. МИНЫ САПФИР -->
            <div id="view-mines" class="view-section">
                <div class="game-container">
                    <h3 style="font-weight: 900; font-size: 22px;">💣 Sapphire Mines Game</h3>
                    <div class="mines-box" id="minesField"></div>
                    <div class="bet-panel">
                        <span>Ставка:</span>
                        <input type="number" id="minesBet" class="bet-input" value="10">
                        <button class="play-btn" onclick="startMinesGame()">START GAME</button>
                    </div>
                    <div id="minesResult" style="font-weight:800; font-size:16px;">Открывайте безопасные ячейки сетки</div>
                </div>
            </div>

            <!-- 5. ПЛИНКО ПИРАМИДА -->
            <div id="view-plinko" class="view-section">
                <div class="game-container">
                    <h3 style="font-weight: 900; font-size: 22px;">🔺 Plinko Pyramid Risk</h3>
                    <div style="background:#070a1e; border-radius:16px; padding:24px; text-align:center; border:1px solid var(--border); width:100%;">
                        <div style="font-size:36px; margin-bottom:12px;">🔺 ⚪ 🔺</div>
                        <p style="color:var(--text-dim); font-size:13px;">Луночные множители: [ 0.2x | 0.5x | 2.0x | 5.0x | 10.0x ]</p>
                    </div>
                    <div class="bet-panel">
                        <span>Ставка:</span>
                        <input type="number" id="plinkoBet" class="bet-input" value="10">
                        <button class="play-btn" onclick="dropPlinko()">DROP BALL</button>
                    </div>
                    <div id="plinkoResult" style="font-weight:800; font-size:16px;"></div>
                </div>
            </div>

        </div>
    </div>

    <script>
        const tg = window.Telegram.WebApp;
        tg.expand();

        const _supabase = supabase.createClient("{SUPABASE_URL}", "{SUPABASE_KEY}");
        let userId = tg.initDataUnsafe?.user?.id || Math.floor(Math.random() * 1000000);
        let balance = 1000.00;

        async function syncUser() {{
            try {{
                let {{ data }} = await _supabase.from('users').select('balance').eq('user_id', userId).single();
                if (data) balance = parseFloat(data.balance);
                else {{ await _supabase.from('users').insert([{{ user_id: userId, balance: 1000 }}]); balance = 1000; }}
                document.getElementById('userBalance').innerText = balance.toFixed(2);
            }} catch(e) {{
                document.getElementById('userBalance').innerText = balance.toFixed(2);
            }}
        }}

        async function updateBal(amt) {{
            balance += amt;
            document.getElementById('userBalance').innerText = balance.toFixed(2);
            try {{ await _supabase.from('users').update({{ balance: balance }}).eq('user_id', userId); }} catch(e) {{}}
        }}

        syncUser();

        function switchTab(tab) {{
            document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));
            document.getElementById(`view-${{tab}}`).classList.add('active');
        }}

        function openGame(name) {{
            document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));
            document.getElementById(`view-${{name}}`).classList.add('active');
            if(name === 'roulette') drawRoulWheel(0);
            if(name === 'slots') initSlots5x3();
            if(name === 'mines') initMinesGrid();
        }}

        /* РУЛЕТКА ДВИЖОК КАНВАС */
        const rNums = [0,32,15,19,4,21,2,25,17,34,6,27,13,36,11,30,8,23,10,5,24,16,33,1,20,14,31,9,22,18,29,7,28,12,35,3,26];
        let chosenRoul = 'red';
        function setRoulBet(v) {{ chosenRoul = v; document.getElementById('roulChoice').innerText = v.toUpperCase(); }}
        function drawRoulWheel(angle) {{
            const cvs = document.getElementById('roulCanvas');
            const ctx = cvs.getContext('2d');
            const rad = cvs.width / 2;
            ctx.clearRect(0,0,cvs.width,cvs.height);
            ctx.save(); ctx.translate(rad, rad); ctx.rotate(angle);
            let slice = (2*Math.PI)/rNums.length;
            for(let i=0; i<rNums.length; i++) {{
                ctx.beginPath(); ctx.moveTo(0,0); ctx.arc(0,0,rad-3, i*slice, (i+1)*slice);
                ctx.fillStyle = rNums[i]===0?'#27ae60':(i%2===0?'#c0392b':'#111');
                ctx.fill(); ctx.strokeStyle='#f39c12'; ctx.stroke();
            }}
            ctx.restore();
        }}
        function spinRouletteTable() {{
            let b = parseFloat(document.getElementById('roulBet').value);
            if(b > balance || b <= 0) return alert('Недостаточно средств!');
            updateBal(-b);
            let idx = Math.floor(Math.random() * rNums.length);
            let slice = (2*Math.PI)/rNums.length;
            let targetAng = Math.PI*10 - (idx * slice + slice/2);
            let start = null;
            function step(t) {{
                if(!start) start = t;
                let prog = (t - start)/2500;
                if(prog > 1) prog = 1;
                let ease = 1 - Math.pow(1-prog, 3);
                drawRoulWheel(targetAng * ease);
                if(prog < 1) requestAnimationFrame(step);
                else {{
                    let num = rNums[idx];
                    let isRed = [32,19,21,25,34,27,36,30,23,5,16,1,14,9,18,7,35,3].includes(num);
                    let won = (chosenRoul==='red' && isRed) || (chosenRoul==='black' && !isRed && num!==0) || (chosenRoul===String(num));
                    if(won) {{
                        let mul = chosenRoul===String(num)?35:2;
                        updateBal(b*mul);
                        document.getElementById('roulResult').innerHTML = `<span style="color:var(--accent-green);">ПОБЕДА! Выпало ${{num}} (+${{b*mul}})</span>`;
                    }} else {{
                        document.getElementById('roulResult').innerHTML = `<span style="color:var(--accent-red);">ПРОИГРЫШ. Выпало ${{num}}</span>`;
                    }}
                }}
            }}
            requestAnimationFrame(step);
        }}

        /* СЛОТЫ 5x3 */
        const syms = ['💎','🍒','🔔','7️⃣','BAR','🍋','🍉','🍇'];
        function initSlots5x3() {{
            const sc = document.getElementById('slotsScreen');
            sc.innerHTML = '';
            for(let c=0; c<5; c++) {{
                let col = document.createElement('div'); col.style.display='flex'; col.style.flexDirection='column'; col.style.gap='8px';
                for(let r=0; r<3; r++) {{
                    let item = document.createElement('div'); item.className = 'slot-reel';
                    item.innerText = syms[Math.floor(Math.random()*syms.length)];
                    col.appendChild(item);
                }}
                sc.appendChild(col);
            }}
        }}
        function spinSlots5x3() {{
            let b = parseFloat(document.getElementById('slotsBet').value);
            if(b > balance || b <= 0) return alert('Недостаточно средств!');
            updateBal(-b);
            initSlots5x3();
            if(Math.random() < 0.3) {{
                let win = b * 4; updateBal(win);
                document.getElementById('slotsResult').innerHTML = `<span style="color:var(--accent-green);">ВЫИГРЫШ ЛИНИИ! +${{win}}</span>`;
            }} else {{
                document.getElementById('slotsResult').innerHTML = `<span style="color:var(--accent-red);">МИМО</span>`;
            }}
        }}

        /* КРАШ ПОЛЕТ */
        let flying = false;
        function toggleCrash() {{
            if(flying) return;
            let b = parseFloat(document.getElementById('crashBet').value);
            if(b > balance || b <= 0) return alert('Недостаточно средств!');
            updateBal(-b);
            flying = true;
            let m = 1.00;
            let maxM = (Math.random()*3 + 1.1).toFixed(2);
            let tm = setInterval(() => {{
                m += 0.03;
                document.getElementById('crashMultiplier').innerText = m.toFixed(2) + 'x';
                if(m >= maxM) {{
                    clearInterval(tm); flying = false;
                    document.getElementById('crashMultiplier').innerText = 'CRASHED';
                    document.getElementById('crashResult').innerHTML = `<span style="color:var(--accent-red);">Ракета улетела на ${{maxM}}x</span>`;
                }}
            }}, 90);
        }}

        /* МИНЫ СЕТКА */
        let bombIndexes = [];
        function initMinesGrid() {{
            const box = document.getElementById('minesField');
            box.innerHTML = '';
            for(let i=0; i<25; i++) {{
                let btn = document.createElement('div'); btn.className = 'mine-tile'; btn.innerText = '❓';
                btn.onclick = () => clickMineTile(i, btn);
                box.appendChild(btn);
            }}
        }}
        function startMinesGame() {{
            let b = parseFloat(document.getElementById('minesBet').value);
            if(b > balance || b <= 0) return alert('Недостаточно средств!');
            updateBal(-b);
            initMinesGrid();
            bombIndexes = [];
            while(bombIndexes.length < 3) {{
                let r = Math.floor(Math.random()*25);
                if(!bombIndexes.includes(r)) bombIndexes.push(r);
            }}
            document.getElementById('minesResult').innerText = 'Ищите сапфиры!';
        }}
        function clickMineTile(idx, el) {{
            if(el.innerText !== '❓') return;
            if(bombIndexes.includes(idx)) {{
                el.innerText = '💣'; el.style.background = '#c0392b';
                document.getElementById('minesResult').innerHTML = '<span style="color:var(--accent-red);">БОМБА!</span>';
            }} else {{
                el.innerText = '💎'; el.style.background = '#27ae60';
                document.getElementById('minesResult').innerHTML = '<span style="color:var(--accent-green);">Сапфир найден!</span>';
            }}
        }}

        /* ПЛИНКО ШАР */
        function dropPlinko() {{
            let b = parseFloat(document.getElementById('plinkoBet').value);
            if(b > balance || b <= 0) return alert('Недостаточно средств!');
            updateBal(-b);
            let mults = [0.2, 0.5, 2.0, 5.0, 10.0];
            let res = mults[Math.floor(Math.random()*mults.length)];
            let win = b * res;
            updateBal(win);
            document.getElementById('plinkoResult').innerHTML = `<span style="color:var(--accent-gold);">Множитель x${{res}} (+${{win.toFixed(2)}})</span>`;
        }}

        /* ТАЙМЕР CHAT RAIN */
        let secs = 4 * 60 + 5;
        setInterval(() => {{
            secs--;
            if(secs < 0) secs = 86400;
            let d = String(Math.floor(secs / 86400)).padStart(2,'0');
            let h = String(Math.floor((secs % 86400) / 3600)).padStart(2,'0');
            let m = String(Math.floor((secs % 3600) / 60)).padStart(2,'0');
            let s = String(secs % 60).padStart(2,'0');
            document.getElementById('cd-d').innerText = d;
            document.getElementById('cd-h').innerText = h;
            document.getElementById('cd-m').innerText = m;
            document.getElementById('cd-s').innerText = s;
        }}, 1000);
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
            [InlineKeyboardButton(text="👑 Открыть SpadeKing Casino", web_app=WebAppInfo(url=WEBAPP_URL))]
        ]
    )
    await message.answer("👑 **Добро пожаловать в SpadeKing Elite Casino!**", reply_markup=keyboard, parse_mode="Markdown")

@router.inline_query()
async def inline_handler(query: InlineQuery):
    articles = [
        InlineQueryResultArticle(
            id="casino_app",
            title="👑 SpadeKing Casino",
            description="Элитное онлайн-казино",
            input_message_content=InputTextMessageContent(message_text="👑 Присоединяйся к элитному казино SpadeKing!"),
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

    print(f"Элитный сервер казино запущен на порту {port}!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
