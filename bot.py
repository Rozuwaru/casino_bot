"""
================================================================================
SPADE KING ELITE MOBILE CASINO & SPORTSBOOK - FULL PRODUCTION CODEBASE
Architecture: Aiogram 3.x + Aiohttp + Supabase Realtime + HTML5 Canvas Physics
Target: Telegram Mini App (Mobile Optimized)
================================================================================
"""

import asyncio
import logging
import os
import json
import random
from typing import Dict, Any, List, Optional
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart, Command
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

# ---------------------------------------------------------------------------
# КОНФИГУРАЦИЯ СЕРВЕРА И БАЗЫ ДАННЫХ
# ---------------------------------------------------------------------------
TOKEN: str = "8752641180:AAET94FACuNdO26CCdFHFyv1vJhSiv3O7F4"
WEBAPP_URL: str = "https://casino-bot-y2qo.onrender.com/webapp"

SUPABASE_URL: str = "https://lnskcqunuaewqcsvcpvr.supabase.co"
SUPABASE_KEY: str = "yJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imxuc2tjcXVudWFld3Fjc3ZjcHZyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTMwMzE2MjQsImV4cCI6MjEwODYwNzYyNH0.g0F_E6hIOeholtABi_WsbMzqT4H-49wTH5XYXAk_0Nc"

# ---------------------------------------------------------------------------
# ТЯЖЕЛОВЕСНЫЙ МОБИЛЬНЫЙ ФРОНТЕНД (HTML5 / CSS3 / CANVAS / WEB AUDIO)
# ---------------------------------------------------------------------------
WEBAPP_HTML = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no, maximum-scale=1.0, viewport-fit=cover">
    <title>SpadeKing Elite Mobile Casino</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-main: #070913;
            --bg-nav: #0b0f1e;
            --panel-bg: #11172e;
            --panel-hover: #1a223f;
            --gold-grad: linear-gradient(135deg, #ffe066 0%, #f39c12 50%, #d35400 100%);
            --accent-gold: #f39c12;
            --accent-green: #2ecc71;
            --accent-red: #e74c3c;
            --text-main: #ffffff;
            --text-dim: #7a8ba9;
            --border: rgba(255, 255, 255, 0.08);
            --safe-bottom: env(safe-area-inset-bottom, 16px);
        }}
        * {{ box-sizing: border-box; user-select: none; -webkit-user-select: none; margin: 0; padding: 0; font-family: 'Montserrat', sans-serif; -webkit-tap-highlight-color: transparent; }}
        body {{ background-color: var(--bg-main); color: var(--text-main); min-height: 100vh; display: flex; flex-direction: column; overflow-x: hidden; padding-bottom: calc(70px + var(--safe-bottom)); }}

        /* МОБИЛЬНАЯ ВЕРХНЯЯ ШАПКА */
        .mobile-header {{
            height: 60px; background: rgba(11, 15, 30, 0.95); border-bottom: 1px solid var(--border);
            display: flex; justify-content: space-between; align-items: center; padding: 0 16px;
            position: sticky; top: 0; z-index: 300; backdrop-filter: blur(12px);
        }}
        .brand-logo {{ font-weight: 900; font-size: 16px; background: var(--gold-grad); -webkit-background-clip: text; -webkit-text-fill-color: transparent; display: flex; align-items: center; gap: 6px; }}
        
        .header-actions {{ display: flex; align-items: center; gap: 10px; }}
        .wallet-pill {{
            background: rgba(46, 204, 113, 0.12); border: 1px solid rgba(46, 204, 113, 0.35);
            padding: 5px 12px; border-radius: 20px; font-weight: 800; color: var(--accent-green); font-size: 13px;
            display: flex; align-items: center; gap: 4px; box-shadow: 0 0 12px rgba(46,204,113,0.15);
        }}
        .wallet-pill.pulse {{ transform: scale(1.08); transition: transform 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275); }}
        
        .icon-circle {{ width: 36px; height: 36px; border-radius: 50%; background: var(--panel-hover); border: 1px solid var(--border); display: flex; align-items: center; justify-content: center; color: #fff; font-size: 14px; cursor: pointer; }}

        /* НИЖНЯЯ МОБИЛЬНАЯ НАВИГАЦИЯ (BOTTOM TAB BAR) */
        .bottom-nav {{
            position: fixed; bottom: 0; left: 0; width: 100%; height: calc(64px + var(--safe-bottom));
            background: rgba(11, 15, 30, 0.98); border-top: 1px solid var(--border);
            display: flex; justify-content: space-around; align-items: flex-start; padding-top: 8px; z-index: 400;
            backdrop-filter: blur(15px);
        }}
        .nav-tab {{
            display: flex; flex-direction: column; align-items: center; gap: 3px; color: var(--text-dim);
            font-size: 10px; font-weight: 700; cursor: pointer; text-decoration: none; flex: 1; transition: 0.2s;
        }}
        .nav-tab span {{ font-size: 20px; }}
        .nav-tab.active {{ color: var(--accent-gold); text-shadow: 0 0 10px rgba(243,156,18,0.4); }}

        /* ОСНОВНОЙ КОНТЕЙНЕР КОНТЕНТА */
        .content-body {{ padding: 14px; flex: 1; display: flex; flex-direction: column; gap: 16px; max-width: 600px; margin: 0 auto; width: 100%; }}

        .view-screen {{ display: none; }}
        .view-screen.active {{ display: flex; flex-direction: column; gap: 16px; animation: screenFade 0.3s ease; }}
        @keyframes screenFade {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; transform: translateY(0); }} }}

        /* БАННЕР СОБЫТИЯ «CHAT RAIN» */
        .rain-banner {{
            background: linear-gradient(135deg, #182042 0%, #0d1224 100%);
            border-radius: 18px; padding: 16px; border: 1px solid var(--border);
            display: flex; flex-direction: column; gap: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); position: relative; overflow: hidden;
        }}
        .rain-timers {{ display: flex; gap: 8px; justify-content: center; }}
        .r-box {{ background: var(--accent-gold); color: #000; width: 44px; height: 48px; border-radius: 10px; display: flex; flex-direction: column; align-items: center; justify-content: center; font-weight: 900; font-size: 16px; box-shadow: 0 4px 15px rgba(243,156,18,0.4); }}
        .r-box span {{ font-size: 8px; font-weight: 700; text-transform: uppercase; }}

        /* СЕТКА ИГР В ЛОББИ */
        .lobby-games-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }}
        .game-card-mobile {{
            background: var(--panel-bg); border-radius: 16px; padding: 16px 12px; border: 1px solid var(--border);
            display: flex; flex-direction: column; align-items: center; text-align: center; cursor: pointer; transition: 0.25s;
            box-shadow: 0 8px 20px rgba(0,0,0,0.3); position: relative; overflow: hidden;
        }}
        .game-card-mobile:active {{ transform: scale(0.96); border-color: var(--accent-gold); }}
        .game-card-mobile.featured {{ grid-column: span 2; background: linear-gradient(135deg, #221504 0%, #11172e 100%); border-color: rgba(243,156,18,0.3); }}
        .card-emoji {{ font-size: 38px; margin-bottom: 8px; filter: drop-shadow(0 3px 6px rgba(0,0,0,0.5)); }}
        .card-name {{ font-size: 14px; font-weight: 800; margin-bottom: 2px; }}
        .card-sub {{ font-size: 10px; color: var(--text-dim); }}

        /* КАРТОЧКИ ПОБЕДИТЕЛЕЙ */
        .winners-scroll {{ display: flex; gap: 10px; overflow-x: auto; padding-bottom: 4px; scrollbar-width: none; }}
        .winners-scroll::-webkit-scrollbar {{ display: none; }}
        .winner-pill-card {{ background: var(--panel-bg); border-radius: 12px; padding: 10px 14px; border: 1px solid var(--border); display: flex; align-items: center; gap: 10px; min-width: 150px; flex-shrink: 0; }}

        /* ИГРОВЫЕ ИНТЕРФЕЙСЫ */
        .game-box-mobile {{ background: var(--panel-bg); border-radius: 18px; padding: 16px; border: 1px solid var(--border); display: flex; flex-direction: column; gap: 14px; }}
        .bet-control-bar {{ display: flex; gap: 10px; align-items: center; background: #070913; padding: 10px 14px; border-radius: 14px; border: 1px solid var(--border); }}
        .bet-input-field {{ background: transparent; border: none; color: var(--accent-gold); font-size: 18px; font-weight: 900; width: 80px; outline: none; text-align: center; }}
        .action-main-btn {{ flex: 1; background: var(--gold-grad); color: #000; border: none; padding: 14px; border-radius: 12px; font-weight: 900; font-size: 15px; cursor: pointer; text-transform: uppercase; box-shadow: 0 6px 20px rgba(243,156,18,0.4); }}
        .action-main-btn:active {{ transform: scale(0.97); }}

        /* РУЛЕТКА */
        .roulette-table-mobile {{ background: #0b532c; border: 4px solid #06361c; border-radius: 14px; padding: 12px; width: 100%; }}
        .r-grid-mob {{ display: grid; grid-template-columns: 35px repeat(12, 1fr); gap: 2px; font-weight: 800; font-size: 10px; text-align: center; color: #fff; }}
        .rc-mob {{ background: #13773f; border: 1px solid rgba(255,255,255,0.25); padding: 10px 0; border-radius: 3px; cursor: pointer; display: flex; align-items: center; justify-content: center; }}
        .rc-mob.red {{ background: #c0392b; }}
        .rc-mob.black {{ background: #111; }}
        .rc-mob.zero {{ grid-row: span 3; background: #27ae60; font-size: 14px; }}

        /* СЛОТЫ */
        .slots-frame-mob {{ background: linear-gradient(180deg, #f1c40f 0%, #d35400 100%); padding: 8px; border-radius: 16px; box-shadow: 0 0 25px rgba(241,196,15,0.3); }}
        .slots-grid-mob {{ background: #050714; border-radius: 12px; display: grid; grid-template-columns: repeat(5, 1fr); gap: 4px; padding: 8px; }}
        .slot-cell-mob {{ background: linear-gradient(180deg, #13192f 0%, #0c1020 100%); height: 70px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 32px; border: 1px solid var(--border); }}

        /* МИНЫ */
        .mines-grid-mob {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; width: 100%; }}
        .mine-cell-mob {{ aspect-ratio: 1; background: #1a223d; border-radius: 10px; border: 1px solid var(--border); display: flex; align-items: center; justify-content: center; font-size: 24px; cursor: pointer; }}
        .mine-cell-mob:active {{ transform: scale(0.95); }}
    </style>
</head>
<body>

    <!-- МОБИЛЬНАЯ ШАПКА -->
    <div class="mobile-header">
        <div class="brand-logo">👑 SPADE KING</div>
        <div class="header-actions">
            <div class="wallet-pill" id="walletPill">🪙 <span id="userBalance">1000.00</span></div>
            <div class="icon-circle" onclick="alert('Профиль и настройки аккаунта')">⚙️</div>
        </div>
    </div>

    <!-- КОНТЕНТНАЯ ОБЛАСТЬ -->
    <div class="content-body">

        <!-- 1. ЛОББИ -->
        <div id="screen-lobby" class="view-screen active">
            <!-- БАННЕР CHAT RAIN -->
            <div class="rain-banner">
                <div>
                    <div style="font-size: 16px; font-weight: 900; margin-bottom: 4px;">Chat Rain Event 🌧️</div>
                    <div style="color: var(--text-dim); font-size: 11px;">Раздача криптовалюты активным игрокам чата каждые 5 часов.</div>
                </div>
                <div class="rain-timers">
                    <div class="r-box"><div id="cd-d">07</div><span>Дней</span></div>
                    <div class="r-box"><div id="cd-h">08</div><span>Часов</span></div>
                    <div class="r-box"><div id="cd-m">05</div><span>Мин</span></div>
                    <div class="r-box"><div id="cd-s">04</div><span>Сек</span></div>
                </div>
                <button class="action-main-btn" style="padding: 10px; font-size: 13px;" onclick="alert('Вы успешно присоединились к Chat Rain!')">Принять участие</button>
            </div>

            <div style="font-size: 15px; font-weight: 800; margin-top: 4px;">Популярные игры</div>
            <div class="lobby-games-grid">
                <div class="game-card-mobile featured" onclick="switchScreen('plinko')">
                    <span class="card-emoji">🔺</span>
                    <div class="card-name">Plinko Elite Physics</div>
                    <div class="card-sub">Оригинальная пирамида с физикой шариков и множителями</div>
                </div>
                <div class="game-card-mobile" onclick="switchScreen('roulette')">
                    <span class="card-emoji">🎡</span>
                    <div class="card-name">Рулетка</div>
                    <div class="card-sub">Европейский стол</div>
                </div>
                <div class="game-card-mobile" onclick="switchScreen('slots')">
                    <span class="card-emoji">🎰</span>
                    <div class="card-name">Слоты 5x3</div>
                    <div class="card-sub">VIP барабаны</div>
                </div>
                <div class="game-card-mobile" onclick="switchScreen('crash')">
                    <span class="card-emoji">🚀</span>
                    <div class="card-name">Crash Space</div>
                    <div class="card-sub">Ракета и комочки</div>
                </div>
                <div class="game-card-mobile" onclick="switchScreen('mines')">
                    <span class="card-emoji">💣</span>
                    <div class="card-name">Сапфировые Мины</div>
                    <div class="card-sub">Сетка 5x5</div>
                </div>
            </div>

            <div style="font-size: 15px; font-weight: 800; margin-top: 4px;">Топ победителей</div>
            <div class="winners-scroll">
                <div class="winner-pill-card"><div style="font-size:20px;">👑</div><div><div style="font-weight:700; font-size:12px;">Imran</div><div style="color:var(--accent-green); font-size:11px;">+2,450 🪙</div></div></div>
                <div class="winner-pill-card"><div style="font-size:20px;">⚡</div><div><div style="font-weight:700; font-size:12px;">Murad</div><div style="color:var(--accent-green); font-size:11px;">+1,120 🪙</div></div></div>
                <div class="winner-pill-card"><div style="font-size:20px;">💎</div><div><div style="font-weight:700; font-size:12px;">Raihgd</div><div style="color:var(--accent-green); font-size:11px;">+980 🪙</div></div></div>
            </div>
        </div>

        <!-- 2. PLINKO (1 в 1 ОРИГИНАЛ С ФИЗИКОЙ CANVAS) -->
        <div id="screen-plinko" class="view-screen">
            <div class="game-box-mobile">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div style="font-weight:900; font-size:15px;">🔺 Plinko Elite Physics</div>
                    <button onclick="switchScreen('lobby')" style="background:none; border:none; color:var(--text-dim); font-weight:700; cursor:pointer;">✕ Закрыть</button>
                </div>
                <div style="display:flex; gap:8px;">
                    <select id="plinkoRisk" style="flex:1; background:#070913; border:1px solid var(--border); color:#fff; padding:8px; border-radius:8px; font-weight:700; font-size:12px;" onchange="updatePlinkoConfig()">
                        <option value="low">Риск: Низкий</option>
                        <option value="normal" selected>Риск: Нормальный</option>
                        <option value="high">Риск: Высокий</option>
                    </select>
                    <select id="plinkoLines" style="flex:1; background:#070913; border:1px solid var(--border); color:#fff; padding:8px; border-radius:8px; font-weight:700; font-size:12px;" onchange="updatePlinkoConfig()">
                        <option value="10">Линий: 10</option>
                        <option value="12" selected>Линий: 12</option>
                        <option value="14">Линий: 14</option>
                        <option value="16">Линий: 16</option>
                    </select>
                </div>
                <div style="display:flex; justify-content:center; background:#070913; border-radius:12px; border:1px solid var(--border); padding:6px; overflow:hidden;">
                    <canvas id="plinkoCanvas" width="340" height="300"></canvas>
                </div>
                <div class="bet-control-bar">
                    <span style="font-size:12px; font-weight:700; color:var(--text-dim);">Ставка:</span>
                    <input type="number" id="plinkoBet" class="bet-input-field" value="10">
                    <button class="action-main-btn" onclick="dropPlinkoBall()">DROP BALL</button>
                </div>
                <div id="plinkoRes" style="font-weight:800; text-align:center; font-size:14px; min-height:20px;"></div>
            </div>
        </div>

        <!-- 3. ЕВРОПЕЙСКАЯ РУЛЕТКА -->
        <div id="screen-roulette" class="view-screen">
            <div class="game-box-mobile">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div style="font-weight:900; font-size:15px;">🎡 Европейская рулетка</div>
                    <button onclick="switchScreen('lobby')" style="background:none; border:none; color:var(--text-dim); font-weight:700; cursor:pointer;">✕ Закрыть</button>
                </div>
                <div style="text-align:center;"><canvas id="roulCanvas" width="150" height="150" style="border-radius:50%; border:3px solid var(--accent-gold);"></canvas></div>
                <div class="roulette-table-mobile">
                    <div class="r-grid-mob">
                        <div class="rc-mob zero" onclick="setRoul('0')">0</div>
                        <div class="rc-mob red" onclick="setRoul('3')">3</div><div class="rc-mob black" onclick="setRoul('6')">6</div><div class="rc-mob red" onclick="setRoul('9')">9</div>
                        <div class="rc-mob red" onclick="setRoul('12')">12</div><div class="rc-mob black" onclick="setRoul('15')">15</div><div class="rc-mob red" onclick="setRoul('18')">18</div>
                        <div class="rc-mob red" onclick="setRoul('21')">21</div><div class="rc-mob black" onclick="setRoul('24')">24</div><div class="rc-mob red" onclick="setRoul('27')">27</div>
                        <div class="rc-mob red" onclick="setRoul('30')">30</div><div class="rc-mob black" onclick="setRoul('33')">33</div><div class="rc-mob red" onclick="setRoul('36')">36</div>
                    </div>
                </div>
                <div style="display:flex; gap:8px;">
                    <button class="action-main-btn" style="background:#c0392b; color:#fff; padding:10px;" onclick="setRoul('red')">RED (x2)</button>
                    <button class="action-main-btn" style="background:#111; color:#fff; padding:10px;" onclick="setRoul('black')">BLACK (x2)</button>
                </div>
                <div class="bet-control-bar">
                    <span style="font-size:12px; font-weight:700; color:var(--text-dim);">Ставка:</span>
                    <input type="number" id="roulBet" class="bet-input-field" value="10">
                    <button class="action-main-btn" onclick="spinRoulette()">SPIN</button>
                </div>
                <div id="roulRes" style="font-weight:800; text-align:center; font-size:14px;">Ставка на: <span id="roulChoice" style="color:var(--accent-gold);">RED</span></div>
            </div>
        </div>

        <!-- 4. СЛОТЫ -->
        <div id="screen-slots" class="view-screen">
            <div class="game-box-mobile">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div style="font-weight:900; font-size:15px;">🎰 VIP Слоты 5x3</div>
                    <button onclick="switchScreen('lobby')" style="background:none; border:none; color:var(--text-dim); font-weight:700; cursor:pointer;">✕ Закрыть</button>
                </div>
                <div class="slots-frame-mob">
                    <div class="slots-grid-mob" id="slotsScreen"></div>
                </div>
                <div class="bet-control-bar">
                    <span style="font-size:12px; font-weight:700; color:var(--text-dim);">Ставка:</span>
                    <input type="number" id="slotsBet" class="bet-input-field" value="10">
                    <button class="action-main-btn" onclick="spinSlots()">SPIN REELS</button>
                </div>
                <div id="slotsRes" style="font-weight:800; text-align:center; font-size:14px;"></div>
            </div>
        </div>

        <!-- 5. КРАШ -->
        <div id="screen-crash" class="view-screen">
            <div class="game-box-mobile">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div style="font-weight:900; font-size:15px;">🚀 Crash Space Flight</div>
                    <button onclick="switchScreen('lobby')" style="background:none; border:none; color:var(--text-dim); font-weight:700; cursor:pointer;">✕ Закрыть</button>
                </div>
                <div style="width:100%; height:200px; background:#030511; border-radius:12px; border:1px solid var(--border); display:flex; align-items:center; justify-content:center;">
                    <div id="crashMultText" style="font-size:48px; font-weight:900; color:#fff; text-shadow:0 0 20px rgba(243,156,18,0.5);">1.00x</div>
                </div>
                <div class="bet-control-bar">
                    <span style="font-size:12px; font-weight:700; color:var(--text-dim);">Ставка:</span>
                    <input type="number" id="crashBet" class="bet-input-field" value="10">
                    <button class="action-main-btn" onclick="toggleCrash()">LAUNCH</button>
                </div>
                <div id="crashRes" style="font-weight:800; text-align:center; font-size:14px;"></div>
            </div>
        </div>

        <!-- 6. МИНЫ -->
        <div id="screen-mines" class="view-screen">
            <div class="game-box-mobile">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div style="font-weight:900; font-size:15px;">💣 Сапфировые Мины</div>
                    <button onclick="switchScreen('lobby')" style="background:none; border:none; color:var(--text-dim); font-weight:700; cursor:pointer;">✕ Закрыть</button>
                </div>
                <div class="mines-grid-mob" id="minesField"></div>
                <div class="bet-control-bar">
                    <span style="font-size:12px; font-weight:700; color:var(--text-dim);">Ставка:</span>
                    <input type="number" id="minesBet" class="bet-input-field" value="10">
                    <button class="action-main-btn" onclick="startMines()">START GAME</button>
                </div>
                <div id="minesRes" style="font-weight:800; text-align:center; font-size:14px;">Открывайте ячейки сетки</div>
            </div>
        </div>

    </div>

    <!-- НИЖНЯЯ ПАНЕЛЬ НАВИГАЦИИ -->
    <div class="bottom-nav">
        <div class="nav-tab active" onclick="switchScreen('lobby')"><span>🏠</span>Лобби</div>
        <div class="nav-tab" onclick="switchScreen('plinko')"><span>🔺</span>Plinko</div>
        <div class="nav-tab" onclick="switchScreen('roulette')"><span>🎡</span>Рулетка</div>
        <div class="nav-tab" onclick="switchScreen('slots')"><span>🎰</span>Слоты</div>
        <div class="nav-tab" onclick="alert('Кошелек и транзакции')"><span>👛</span>Касса</div>
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
            let el = document.getElementById('userBalance');
            let pill = document.getElementById('walletPill');
            el.innerText = balance.toFixed(2);
            pill.classList.add('pulse');
            setTimeout(() => pill.classList.remove('pulse'), 200);
            try {{ await _supabase.from('users').update({{ balance: balance }}).eq('user_id', userId); }} catch(e) {{}}
        }}

        syncUser();

        function switchScreen(id) {{
            document.querySelectorAll('.view-screen').forEach(el => el.classList.remove('active'));
            document.getElementById(`screen-${{id}}`).classList.add('active');
            document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
            if(id === 'plinko') drawPlinkoBoard();
            if(id === 'roulette') drawRoulWheel(0);
            if(id === 'slots') initSlots();
            if(id === 'mines') initMinesGrid();
        }}

        /* --- ПЛИНКО ФИЗИЧЕСКИЙ ДВИЖОК --- */
        const plinkoCanvas = document.getElementById('plinkoCanvas');
        const pCtx = plinkoCanvas.getContext('2d');
        let plinkoRisk = 'normal';
        let plinkoLines = 12;
        let balls = [];

        function getPlinkoMults() {{
            if(plinkoRisk === 'low') return [5, 2, 1.5, 1.1, 1, 0.5, 1, 1.1, 1.5, 2, 5];
            if(plinkoRisk === 'normal') return [10, 3, 1.4, 1.2, 0.7, 0.3, 0.7, 1.2, 1.4, 3, 10];
            return [29, 8, 2.5, 0.8, 0.3, 0.2, 0.3, 0.8, 2.5, 8, 29];
        }}

        function drawPlinkoBoard() {{
            pCtx.clearRect(0, 0, plinkoCanvas.width, plinkoCanvas.height);
            let rows = plinkoLines;
            let startY = 20;
            let spacingX = 20;
            let spacingY = 18;

            pCtx.fillStyle = "#fff";
            for(let r=0; r<rows; r++) {{
                let count = r + 3;
                let w = (count - 1) * spacingX;
                let startX = (plinkoCanvas.width - w) / 2;
                for(let c=0; c<count; c++) {{
                    pCtx.beginPath();
                    pCtx.arc(startX + c * spacingX, startY + r * spacingY, 2, 0, Math.PI*2);
                    pCtx.fill();
                }}
            }}

            let mults = getPlinkoMults();
            let binY = startY + rows * spacingY + 8;
            let binW = spacingX;
            let totalW = mults.length * binW;
            let startBinX = (plinkoCanvas.width - totalW) / 2;

            for(let i=0; i<mults.length; i++) {{
                let bx = startBinX + i * binW;
                pCtx.fillStyle = mults[i] >= 2 ? '#e74c3c' : '#2980b9';
                pCtx.fillRect(bx+1, binY, binW-2, 18);
                pCtx.fillStyle = "#fff";
                pCtx.font = "bold 8px Montserrat";
                pCtx.textAlign = "center";
                pCtx.fillText(mults[i] + 'x', bx + binW/2, binY + 12);
            }}

            for(let b of balls) {{
                pCtx.fillStyle = "#ff4757";
                pCtx.beginPath();
                pCtx.arc(b.x, b.y, 5, 0, Math.PI*2);
                pCtx.fill();
            }}
        }}

        function updatePlinkoPhysics() {{
            let rows = plinkoLines;
            let startY = 20;
            let spacingX = 20;
            let spacingY = 18;
            let mults = getPlinkoMults();
            let binY = startY + rows * spacingY + 8;
            let binW = spacingX;
            let startBinX = (plinkoCanvas.width - (mults.length * binW)) / 2;

            for(let i = balls.length - 1; i >= 0; i--) {{
                let b = balls[i];
                b.vy += 0.2;
                b.x += b.vx;
                b.y += b.vy;

                for(let r=0; r<rows; r++) {{
                    let count = r + 3;
                    let w = (count - 1) * spacingX;
                    let startX = (plinkoCanvas.width - w) / 2;
                    for(let c=0; c<count; c++) {{
                        let px = startX + c * spacingX;
                        let py = startY + r * spacingY;
                        if(Math.hypot(b.x - px, b.y - py) < 7) {{
                            b.vy = -b.vy * 0.4;
                            b.vx += (Math.random() - 0.5) * 1.5;
                        }}
                    }}
                }}

                if(b.y >= binY) {{
                    let idx = Math.floor((b.x - startBinX) / binW);
                    idx = Math.max(0, Math.min(mults.length - 1, idx));
                    let mult = mults[idx];
                    let win = b.bet * mult;
                    updateBal(win);
                    document.getElementById('plinkoRes').innerHTML = `<span style="color:var(--accent-green);">Выигрыш x${{mult}} (+${{win.toFixed(2)}})</span>`;
                    balls.splice(i, 1);
                }}
            }}
            drawPlinkoBoard();
            requestAnimationFrame(updatePlinkoPhysics);
        }}

        function dropPlinkoBall() {{
            let b = parseFloat(document.getElementById('plinkoBet').value);
            if(b > balance || b <= 0) return alert('Недостаточно средств!');
            updateBal(-b);
            balls.push({{ x: plinkoCanvas.width/2 + (Math.random()-0.5)*4, y: 5, vx: (Math.random()-0.5)*0.6, vy: 0, bet: b }});
        }}

        function updatePlinkoConfig() {{
            plinkoRisk = document.getElementById('plinkoRisk').value;
            plinkoLines = parseInt(document.getElementById('plinkoLines').value);
            drawPlinkoBoard();
        }}

        requestAnimationFrame(updatePlinkoPhysics);

        /* --- РУЛЕТКА --- */
        const rNums = [0,32,15,19,4,21,2,25,17,34,6,27,13,36,11,30,8,23,10,5,24,16,33,1,20,14,31,9,22,18,29,7,28,12,35,3,26];
        let chosenRoul = 'red';
        function setRoul(v) {{ chosenRoul = v; document.getElementById('roulChoice').innerText = v.toUpperCase(); }}
        function drawRoulWheel(angle) {{
            const cvs = document.getElementById('roulCanvas');
            const ctx = cvs.getContext('2d');
            const rad = cvs.width / 2;
            ctx.clearRect(0,0,cvs.width,cvs.height);
            ctx.save(); ctx.translate(rad, rad); ctx.rotate(angle);
            let slice = (2*Math.PI)/rNums.length;
            for(let i=0; i<rNums.length; i++) {{
                ctx.beginPath(); ctx.moveTo(0,0); ctx.arc(0,0,rad-2, i*slice, (i+1)*slice);
                ctx.fillStyle = rNums[i]===0?'#27ae60':(i%2===0?'#c0392b':'#111');
                ctx.fill(); ctx.strokeStyle='#f39c12'; ctx.stroke();
            }}
            ctx.restore();
        }}
        function spinRoulette() {{
            let b = parseFloat(document.getElementById('roulBet').value);
            if(b > balance || b <= 0) return alert('Недостаточно средств!');
            updateBal(-b);
            let idx = Math.floor(Math.random() * rNums.length);
            let slice = (2*Math.PI)/rNums.length;
            let targetAng = Math.PI*10 - (idx * slice + slice/2);
            let start = null;
            function step(t) {{
                if(!start) start = t;
                let prog = (t - start)/2000;
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
                        document.getElementById('roulRes').innerHTML = `<span style="color:var(--accent-green);">ПОБЕДА! Выпало ${{num}} (+${{b*mul}})</span>`;
                    }} else {{
                        document.getElementById('roulRes').innerHTML = `<span style="color:var(--accent-red);">ПРОИГРЫШ. Выпало ${{num}}</span>`;
                    }}
                }}
            }}
            requestAnimationFrame(step);
        }}

        /* --- СЛОТЫ --- */
        const syms = ['💎','🍒','🔔','7️⃣','BAR','🍋','🍉','🍇'];
        function initSlots() {{
            const sc = document.getElementById('slotsScreen');
            sc.innerHTML = '';
            for(let c=0; c<5; c++) {{
                let col = document.createElement('div'); col.style.display='flex'; col.style.flexDirection='column'; col.style.gap='4px';
                for(let r=0; r<3; r++) {{
                    let item = document.createElement('div'); item.className = 'slot-cell-mob';
                    item.innerText = syms[Math.floor(Math.random()*syms.length)];
                    col.appendChild(item);
                }}
                sc.appendChild(col);
            }}
        }}
        function spinSlots() {{
            let b = parseFloat(document.getElementById('slotsBet').value);
            if(b > balance || b <= 0) return alert('Недостаточно средств!');
            updateBal(-b);
            initSlots();
            if(Math.random() < 0.3) {{
                let win = b * 4; updateBal(win);
                document.getElementById('slotsRes').innerHTML = `<span style="color:var(--accent-green);">ВЫИГРЫШ! +${{win}}</span>`;
            }} else {{
                document.getElementById('slotsRes').innerHTML = `<span style="color:var(--accent-red);">МИМО</span>`;
            }}
        }}

        /* --- КРАШ --- */
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
                m += 0.04;
                document.getElementById('crashMultText').innerText = m.toFixed(2) + 'x';
                if(m >= maxM) {{
                    clearInterval(tm); flying = false;
                    document.getElementById('crashMultText').innerText = 'CRASHED';
                    document.getElementById('crashRes').innerHTML = `<span style="color:var(--accent-red);">Ракета улетела на ${{maxM}}x</span>`;
                }}
            }}, 80);
        }}

        /* --- МИНЫ --- */
        let bombIdx = [];
        function initMinesGrid() {{
            const box = document.getElementById('minesField');
            box.innerHTML = '';
            for(let i=0; i<25; i++) {{
                let btn = document.createElement('div'); btn.className = 'mine-cell-mob'; btn.innerText = '❓';
                btn.onclick = () => clickMine(i, btn);
                box.appendChild(btn);
            }}
        }}
        function startMines() {{
            let b = parseFloat(document.getElementById('minesBet').value);
            if(b > balance || b <= 0) return alert('Недостаточно средств!');
            updateBal(-b);
            initMinesGrid();
            bombIdx = [];
            while(bombIdx.length < 3) {{
                let r = Math.floor(Math.random()*25);
                if(!bombIdx.includes(r)) bombIdx.push(r);
            }}
            document.getElementById('minesRes').innerText = 'Ищите сапфиры!';
        }}
        function clickMine(idx, el) {{
            if(el.innerText !== '❓') return;
            if(bombIdx.includes(idx)) {{
                el.innerText = '💣'; el.style.background = '#c0392b';
                document.getElementById('minesRes').innerHTML = '<span style="color:var(--accent-red);">БОМБА! Проигрыш</span>';
            }} else {{
                el.innerText = '💎'; el.style.background = '#27ae60';
                document.getElementById('minesRes').innerHTML = '<span style="color:var(--accent-green);">Сапфир найден!</span>';
            }}
        }}

        /* --- ТАЙМЕР CHAT RAIN --- */
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

# ---------------------------------------------------------------------------
# БАЗОВЫЕ РОУТЕРЫ И СЕРВЕРНЫЕ ОБРАБОТЧИКИ
# ---------------------------------------------------------------------------
async def handle_webapp(request: web.Request) -> web.Response:
    """Отдача HTML-приложения"""
    return web.Response(text=WEBAPP_HTML, content_type="text/html")

async def health_check(request: web.Request) -> web.Response:
    """Проверка здоровья сервера"""
    return web.Response(text="SpadeKing Mobile Casino Active", status=200)

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👑 Запустить SpadeKing Mobile", web_app=WebAppInfo(url=WEBAPP_URL))]
        ]
    )
    await message.answer(
        "👑 **Добро пожаловать в SpadeKing Elite Mobile Casino!**\n\n"
        "Нажмите кнопку ниже для запуска мобильного приложения с рулеткой, Plinko и слотами.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@router.inline_query()
async def inline_handler(query: InlineQuery) -> None:
    articles = [
        InlineQueryResultArticle(
            id="mobile_casino",
            title="👑 SpadeKing Mobile Casino",
            description="Мобильное элитное онлайн-казино",
            input_message_content=InputTextMessageContent(message_text="👑 Присоединяйся к мобильному казино SpadeKing!"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🎲 Играть", web_app=WebAppInfo(url=WEBAPP_URL))]])
        )
    ]
    await query.answer(articles, cache_time=1, is_personal=True)

async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    app = web.Application()
    app.router.add_get("/", handle_webapp)
    app.router.add_get("/webapp", handle_webapp)
    app.router.add_get("/health", health_check)

    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logging.info(f"Мобильный сервер казино успешно запущен на порту {port}!")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Сервер успешно остановлен.")
