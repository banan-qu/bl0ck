import os
import sqlite3
import random
import string
import json
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "super-secret-change-me")
socketio = SocketIO(app, async_mode="threading", cors_allowed_origins="*")

DB_NAME = 'blok.db'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

THEMES = {
    'default': {'name': 'Углерод', 'bg': '#0b0b0d', 'card': 'rgba(18,18,22,0.92)', 'panel': 'rgba(24,24,30,0.92)', 'text': '#f5f5f7', 'muted': '#a7a7ad', 'accent': '#ff3b3b', 'accent_text': '#ffffff', 'border': 'rgba(255,59,59,0.22)', 'pattern': 'radial-gradient(circle at 20% 10%, rgba(255,59,59,0.08), transparent 35%)', 'decor': ''},
    'yellow_blue': {'name': 'Солнечный бриз', 'bg': '#071019', 'card': 'rgba(10,22,34,0.9)', 'panel': 'rgba(14,28,42,0.9)', 'text': '#f4fbff', 'muted': '#9ec3dd', 'accent': '#ffd84d', 'accent_text': '#102030', 'border': 'rgba(255,216,77,0.25)', 'pattern': 'linear-gradient(135deg, rgba(0,120,255,0.08), rgba(255,216,77,0.06))', 'decor': ''},
    'green_brown': {'name': 'Лесной мох', 'bg': '#0a120d', 'card': 'rgba(16,28,21,0.9)', 'panel': 'rgba(20,35,26,0.9)', 'text': '#f2fff7', 'muted': '#a6c0ae', 'accent': '#66d98b', 'accent_text': '#082012', 'border': 'rgba(102,217,139,0.22)', 'pattern': 'repeating-linear-gradient(135deg, rgba(102,217,139,0.03) 0 8px, transparent 8px 16px)', 'decor': ''},
    'yellow_black': {'name': 'Промсигнал', 'bg': '#090909', 'card': 'rgba(17,17,17,0.92)', 'panel': 'rgba(24,24,24,0.92)', 'text': '#fffef5', 'muted': '#cfcaa0', 'accent': '#ffe600', 'accent_text': '#111111', 'border': 'rgba(255,230,0,0.25)', 'pattern': 'repeating-linear-gradient(-45deg, rgba(255,230,0,0.05) 0 10px, transparent 10px 20px)', 'decor': ''},
    'turquoise_burgundy': {'name': 'Морской гранат', 'bg': '#081112', 'card': 'rgba(12,24,26,0.9)', 'panel': 'rgba(16,30,33,0.9)', 'text': '#f2fffd', 'muted': '#9dc1c4', 'accent': '#39d0c7', 'accent_text': '#062322', 'border': 'rgba(57,208,199,0.22)', 'pattern': 'radial-gradient(circle at 80% 20%, rgba(120,30,60,0.12), transparent 30%)', 'decor': ''},
    'orange_grey': {'name': 'Медный закат', 'bg': '#120d08', 'card': 'rgba(28,21,14,0.9)', 'panel': 'rgba(36,27,18,0.9)', 'text': '#fff7ee', 'muted': '#c6ab90', 'accent': '#ff9a3d', 'accent_text': '#2a1400', 'border': 'rgba(255,154,61,0.22)', 'pattern': 'linear-gradient(180deg, rgba(255,154,61,0.06), transparent 45%)', 'decor': ''},
    'dark_classic': {'name': 'Графит', 'bg': '#050505', 'card': 'rgba(12,12,12,0.92)', 'panel': 'rgba(18,18,18,0.92)', 'text': '#e8e8e8', 'muted': '#8a8a8a', 'accent': '#8f8f8f', 'accent_text': '#101010', 'border': 'rgba(255,255,255,0.1)', 'pattern': 'repeating-linear-gradient(0deg, rgba(255,255,255,0.015) 0 1px, transparent 1px 4px)', 'decor': ''},
    'light': {'name': 'Фарфор', 'bg': '#f3f5f8', 'card': 'rgba(255,255,255,0.92)', 'panel': 'rgba(250,251,253,0.95)', 'text': '#111827', 'muted': '#667085', 'accent': '#2563eb', 'accent_text': '#ffffff', 'border': 'rgba(17,24,39,0.1)', 'pattern': 'radial-gradient(circle at 10% 10%, rgba(37,99,235,0.06), transparent 28%)', 'decor': ''},

    # Premium themes
    'purple_pink': {'name': 'Неоновая орхидея', 'bg': '#120818', 'card': 'rgba(34,16,44,0.82)', 'panel': 'rgba(44,20,56,0.84)', 'text': '#fff2ff', 'muted': '#d7aee8', 'accent': '#ff5ecb', 'accent_text': '#2b0020', 'border': 'rgba(255,94,203,0.35)', 'pattern': 'radial-gradient(circle at 15% 20%, rgba(255,94,203,0.18), transparent 30%), radial-gradient(circle at 85% 75%, rgba(153,51,255,0.2), transparent 35%), repeating-linear-gradient(135deg, rgba(255,255,255,0.02) 0 6px, transparent 6px 14px)', 'decor': "<div style='position:fixed;left:8px;top:12vh;width:3px;height:76vh;background:linear-gradient(180deg,transparent,#ff5ecb,#9933ff,transparent);opacity:0.35;pointer-events:none;filter:blur(1px)'></div><div style='position:fixed;right:8px;top:12vh;width:3px;height:76vh;background:linear-gradient(180deg,transparent,#9933ff,#ff5ecb,transparent);opacity:0.35;pointer-events:none;filter:blur(1px)'></div>"},
    'bw_pattern': {'name': 'Монохром Матрикс', 'bg': '#020202', 'card': 'rgba(10,10,10,0.86)', 'panel': 'rgba(16,16,16,0.88)', 'text': '#f5f5f5', 'muted': '#bdbdbd', 'accent': '#ffffff', 'accent_text': '#000000', 'border': 'rgba(255,255,255,0.28)', 'pattern': 'repeating-linear-gradient(45deg, rgba(255,255,255,0.06) 0 2px, rgba(0,0,0,0.0) 2px 6px), repeating-linear-gradient(-45deg, rgba(255,255,255,0.03) 0 1px, transparent 1px 8px), radial-gradient(circle at 50% 0%, rgba(255,255,255,0.08), transparent 45%)', 'decor': "<div style='position:fixed;inset:0;pointer-events:none;opacity:0.08;background:linear-gradient(180deg,rgba(255,255,255,0.2),transparent 20%,transparent 80%,rgba(255,255,255,0.15))'></div>"},
    'snow_blue': {'name': 'Арктический лёд', 'bg': '#04101f', 'card': 'rgba(8,26,46,0.78)', 'panel': 'rgba(12,34,58,0.82)', 'text': '#eff8ff', 'muted': '#b5d7f5', 'accent': '#7dd3fc', 'accent_text': '#04243a', 'border': 'rgba(125,211,252,0.32)', 'pattern': 'radial-gradient(circle at 20% 15%, rgba(125,211,252,0.18), transparent 28%), radial-gradient(circle at 80% 70%, rgba(255,255,255,0.12), transparent 26%), repeating-linear-gradient(135deg, rgba(255,255,255,0.025) 0 8px, transparent 8px 18px)', 'decor': "<div style='position:fixed;left:8px;top:0;height:100vh;writing-mode:vertical-rl;opacity:0.22;pointer-events:none;font-size:14px;letter-spacing:10px;color:#dff4ff;text-shadow:0 0 8px rgba(125,211,252,0.5)'>❄ ❅ ❆ ❄ ❅ ❆ ❄ ❅</div><div style='position:fixed;right:8px;top:0;height:100vh;writing-mode:vertical-rl;opacity:0.22;pointer-events:none;font-size:14px;letter-spacing:10px;color:#dff4ff;text-shadow:0 0 8px rgba(125,211,252,0.5)'>❄ ❅ ❆ ❄ ❅ ❆ ❄ ❅</div>"},
    'dark_knight': {'name': 'Готический бастион', 'bg': '#070607', 'card': 'rgba(20,12,14,0.84)', 'panel': 'rgba(28,16,18,0.86)', 'text': '#fff3f3', 'muted': '#d1a7ad', 'accent': '#b3002d', 'accent_text': '#ffffff', 'border': 'rgba(179,0,45,0.35)', 'pattern': 'radial-gradient(circle at 50% 0%, rgba(179,0,45,0.18), transparent 35%), repeating-linear-gradient(135deg, rgba(255,255,255,0.015) 0 6px, transparent 6px 14px)', 'decor': "<div style='position:fixed;left:10px;top:0;height:100vh;writing-mode:vertical-rl;opacity:0.16;pointer-events:none;font-size:18px;letter-spacing:14px;filter:drop-shadow(0 0 6px rgba(179,0,45,0.35))'>🦇 🦇 🦇 🦇 🦇</div><div style='position:fixed;right:10px;top:0;height:100vh;writing-mode:vertical-rl;opacity:0.16;pointer-events:none;font-size:18px;letter-spacing:14px;filter:drop-shadow(0 0 6px rgba(179,0,45,0.35))'>🦇 🦇 🦇 🦇 🦇</div>"},
    'tricolor': {'name': 'Имперский триколор', 'bg': '#121826', 'card': 'rgba(16,22,38,0.84)', 'panel': 'rgba(22,30,50,0.86)', 'text': '#ffffff', 'muted': '#d6d8e3', 'accent': '#1d4ed8', 'accent_text': '#ffffff', 'border': 'rgba(255,255,255,0.22)', 'pattern': 'linear-gradient(180deg, rgba(255,255,255,0.22) 0%, rgba(255,255,255,0.22) 33.33%, rgba(29,78,216,0.28) 33.33%, rgba(29,78,216,0.28) 66.66%, rgba(220,38,38,0.28) 66.66%, rgba(220,38,38,0.28) 100%), radial-gradient(circle at 50% 20%, rgba(255,215,0,0.08), transparent 35%)', 'decor': "<svg style='position:fixed;left:2px;top:0;height:100vh;width:54px;opacity:0.2;pointer-events:none;filter:drop-shadow(0 0 8px rgba(255,215,0,0.25))' viewBox='0 0 60 400' preserveAspectRatio='xMidYMid meet'><path d='M30 50 L25 80 L15 90 L25 100 L20 130 L30 110 L40 130 L35 100 L45 90 L35 80 Z' fill='#ffd700'/></svg><svg style='position:fixed;right:2px;top:0;height:100vh;width:54px;opacity:0.2;pointer-events:none;filter:drop-shadow(0 0 8px rgba(255,215,0,0.25))' viewBox='0 0 60 400' preserveAspectRatio='xMidYMid meet'><path d='M30 50 L25 80 L15 90 L25 100 L20 130 L30 110 L40 130 L35 100 L45 90 L35 80 Z' fill='#ffd700'/></svg>"},
    'blakytno_zhovt': {'name': 'Стяг свободы', 'bg': '#00366f', 'card': 'rgba(6,26,56,0.82)', 'panel': 'rgba(10,34,70,0.85)', 'text': '#ffffff', 'muted': '#eaf2ff', 'accent': '#ffd400', 'accent_text': '#10203a', 'border': 'rgba(255,212,0,0.38)', 'pattern': 'linear-gradient(180deg, #0057b7 0%, #0057b7 50%, #ffd700 50%, #ffd700 100%), radial-gradient(circle at 50% 0%, rgba(255,255,255,0.12), transparent 40%)', 'decor': "<div style='position:fixed;left:10px;top:28vh;opacity:0.3;pointer-events:none;font-size:28px;color:#ffd700;text-shadow:0 0 10px rgba(255,215,0,0.45)'>✦</div><div style='position:fixed;right:10px;top:28vh;opacity:0.3;pointer-events:none;font-size:28px;color:#ffd700;text-shadow:0 0 10px rgba(255,215,0,0.45)'>✦</div><svg style='position:fixed;left:6px;top:38vh;width:38px;height:38px;opacity:0.25;pointer-events:none' viewBox='0 0 40 40'><path d='M20 5 L22 15 L32 12 L25 20 L32 28 L22 25 L20 35 L18 25 L8 28 L15 20 L8 12 L18 15 Z' fill='#ffd700'/></svg><svg style='position:fixed;right:6px;top:38vh;width:38px;height:38px;opacity:0.25;pointer-events:none' viewBox='0 0 40 40'><path d='M20 5 L22 15 L32 12 L25 20 L32 28 L22 25 L20 35 L18 25 L8 28 L15 20 L8 12 L18 15 Z' fill='#ffd700'/></svg>"},
    'stars_stripes': {'name': 'Звёздный штандарт', 'bg': '#061933', 'card': 'rgba(8,24,52,0.82)', 'panel': 'rgba(12,32,66,0.84)', 'text': '#ffffff', 'muted': '#d0d8e8', 'accent': '#d61f3c', 'accent_text': '#ffffff', 'border': 'rgba(255,255,255,0.22)', 'pattern': 'repeating-linear-gradient(0deg, rgba(214,31,60,0.22) 0px, rgba(214,31,60,0.22) 16px, rgba(255,255,255,0.06) 16px, rgba(255,255,255,0.06) 32px), radial-gradient(circle at 15% 15%, rgba(255,255,255,0.08), transparent 22%)', 'decor': "<div style='position:fixed;left:8px;top:10vh;color:rgba(255,255,255,0.28);font-size:14px;line-height:18px;pointer-events:none;text-shadow:0 0 6px rgba(255,255,255,0.2)'>★<br>★ ★<br>★ ★ ★</div><div style='position:fixed;right:8px;top:10vh;color:rgba(255,255,255,0.28);font-size:14px;line-height:18px;pointer-events:none;text-align:right;text-shadow:0 0 6px rgba(255,255,255,0.2)'>★<br>★ ★<br>★ ★ ★</div>"},
    'golden_age': {'name': 'Золотой Ренессанс', 'bg': '#171006', 'card': 'rgba(40,28,10,0.82)', 'panel': 'rgba(52,36,14,0.84)', 'text': '#fff4d6', 'muted': '#d8c08a', 'accent': '#f0c14b', 'accent_text': '#2b1b00', 'border': 'rgba(240,193,75,0.35)', 'pattern': 'radial-gradient(circle at 20% 10%, rgba(240,193,75,0.16), transparent 28%), radial-gradient(circle at 80% 80%, rgba(255,232,170,0.1), transparent 30%), repeating-linear-gradient(45deg, rgba(240,193,75,0.03) 0 8px, transparent 8px 18px)', 'decor': "<div style='position:fixed;left:10px;top:18vh;color:rgba(240,193,75,0.25);font-size:20px;pointer-events:none;text-shadow:0 0 10px rgba(240,193,75,0.25)'>◆<br>◇<br>◆</div><div style='position:fixed;right:10px;top:18vh;color:rgba(240,193,75,0.25);font-size:20px;pointer-events:none;text-shadow:0 0 10px rgba(240,193,75,0.25)'>◆<br>◇<br>◆</div>"},
    'rainbow': {'name': 'Спектрум Прайм', 'bg': '#12091f', 'card': 'rgba(18,16,34,0.78)', 'panel': 'rgba(24,22,44,0.82)', 'text': '#ffffff', 'muted': '#e3dcff', 'accent': '#ff4fd8', 'accent_text': '#1b0620', 'border': 'rgba(255,255,255,0.28)', 'pattern': 'linear-gradient(135deg, rgba(255,0,76,0.22) 0%, rgba(255,136,0,0.2) 18%, rgba(255,230,0,0.18) 34%, rgba(0,214,143,0.18) 52%, rgba(0,153,255,0.2) 70%, rgba(138,43,226,0.22) 86%, rgba(255,79,216,0.2) 100%), radial-gradient(circle at 50% 20%, rgba(255,255,255,0.1), transparent 35%)', 'decor': "<div style='position:fixed;inset:0;pointer-events:none;background:linear-gradient(90deg,rgba(255,0,0,0.05),rgba(255,165,0,0.04),rgba(255,255,0,0.03),rgba(0,255,0,0.03),rgba(0,136,255,0.04),rgba(128,0,255,0.05));mix-blend-mode:screen;opacity:0.8'></div>"}
}

PREMIUM_THEMES = {'purple_pink': 0, 'bw_pattern': 0, 'snow_blue': 0, 'dark_knight': 0, 'tricolor': 0, 'blakytno_zhovt': 0, 'stars_stripes': 0, 'golden_age': 0, 'rainbow': 0}

MARKET_THEMES = {'cosmos': {'name': 'Космос', 'price': 1500, 'theme': {'bg': '#000011', 'card': '#000022', 'panel': '#000033', 'text': '#ffffff', 'muted': '#aaaaff', 'accent': '#6666ff', 'accent_text': '#ffffff', 'border': '#3333aa', 'pattern': 'none', 'decor': ''}}, 'neon_city': {'name': 'Неон-сити', 'price': 2000, 'theme': {'bg': '#0a0014', 'card': '#140a1f', 'panel': '#1a102a', 'text': '#ffffff', 'muted': '#cc99ff', 'accent': '#ff00ff', 'accent_text': '#ffffff', 'border': '#6600aa', 'pattern': 'none', 'decor': ''}}, 'taiga': {'name': 'Тайга', 'price': 1200, 'theme': {'bg': '#0a140a', 'card': '#0f190f', 'panel': '#141f14', 'text': '#ffffff', 'muted': '#a0c0a0', 'accent': '#00ff66', 'accent_text': '#000000', 'border': '#2a4030', 'pattern': 'none', 'decor': ''}}, 'depth': {'name': 'Глубина', 'price': 1800, 'theme': {'bg': '#000814', 'card': '#001020', 'panel': '#001830', 'text': '#ffffff', 'muted': '#6699cc', 'accent': '#0066ff', 'accent_text': '#ffffff', 'border': '#003366', 'pattern': 'none', 'decor': ''}}}

PREMIUM_EMOJIS_MARKET = {'🐉': 500, '🌙': 600, '🍀': 700, '☠️': 800, '🦅': 850, '🚀': 900}

LEGENDARY_USERNAMES = {'banan': 1488, '67': 670, 'fakc': 777, 'admin': 1337, 'bibikar': 2000}

BASE_REACTIONS = ['❤️', '👍', '👎', '💘', '🤡', '🤔']
PREMIUM_REACTIONS = ['xD', '🍌']
RARE_REACTIONS = ['🍆']
STICKERS = ['😂', '😍', '🔥', '👍', '😢', '🤡', '🎉', '😎', '🥲', '🤯']

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        login TEXT UNIQUE,
        password_hash TEXT,
        username TEXT,
        bio TEXT DEFAULT '',
        avatar TEXT DEFAULT '',
        theme TEXT DEFAULT 'default',
        balance INTEGER DEFAULT 0,
        premium INTEGER DEFAULT 0,
        premium_emoji TEXT DEFAULT '',
        banner TEXT DEFAULT '',
        verified INTEGER DEFAULT 0,
        is_admin INTEGER DEFAULT 0,
        blocked INTEGER DEFAULT 0,
        is_online INTEGER DEFAULT 0,
        free_nft_used INTEGER DEFAULT 0,
        owned_themes TEXT DEFAULT '',
        owned_emojis TEXT DEFAULT ''
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS private_chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user1_id INTEGER,
        user2_id INTEGER
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        sender_id INTEGER,
        content TEXT,
        type TEXT DEFAULT 'text',
        reply_to INTEGER DEFAULT NULL,
        is_photo INTEGER DEFAULT 0,
        is_sticker INTEGER DEFAULT 0,
        is_deleted INTEGER DEFAULT 0,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS reactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message_id INTEGER,
        user_id INTEGER,
        reaction TEXT
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS user_usernames (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        uname TEXT UNIQUE,
        score INTEGER,
        reason TEXT,
        rarity TEXT,
        is_nft INTEGER DEFAULT 0,
        for_sale INTEGER DEFAULT 0,
        sale_price INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS blocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        blocker_id INTEGER,
        blocked_id INTEGER
    )''')
    
    # Try to add columns if missing
    try:
        cur.execute("ALTER TABLE users ADD COLUMN login TEXT")
    except:
        pass
    try:
        cur.execute("ALTER TABLE users ADD COLUMN free_nft_used INTEGER DEFAULT 0")
    except:
        pass
    try:
        cur.execute("ALTER TABLE users ADD COLUMN owned_themes TEXT DEFAULT ''")
    except:
        pass
    try:
        cur.execute("ALTER TABLE users ADD COLUMN owned_emojis TEXT DEFAULT ''")
    except:
        pass
    try:
        cur.execute("ALTER TABLE users ADD COLUMN premium_emoji TEXT DEFAULT ''")
    except:
        pass
    
    conn.commit()
    conn.close()

init_db()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        conn.close()
        if user and user['blocked']:
            return redirect(url_for('blocked'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    if 'user_id' not in session:
        return None
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    return user

def get_theme_data(theme_key):
    if theme_key in THEMES:
        t = THEMES[theme_key].copy()
        return t
    if theme_key in MARKET_THEMES:
        mt = MARKET_THEMES[theme_key]
        # merge with defaults
        base = THEMES['default'].copy()
        base.update(mt.get('theme', {}))
        base['name'] = mt['name']
        return base
    return THEMES['default'].copy()

@app.context_processor
def inject_theme():
    user = get_current_user()
    if user:
        theme_key = user['theme'] if user['theme'] else 'default'
        theme = get_theme_data(theme_key)
        return dict(theme=theme, current_user=user, all_themes_global=THEMES, market_themes_global=MARKET_THEMES)
    return dict(theme=THEMES['default'].copy(), current_user=None, all_themes_global=THEMES, market_themes_global=MARKET_THEMES)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def calculate_username_score(uname):
    uname_clean = uname.lower()
    if uname_clean in LEGENDARY_USERNAMES:
        return LEGENDARY_USERNAMES[uname_clean], ['Легендарный фиксированный счёт']
    
    score = 0
    reasons = []
    
    # Length bonus (shorter is better)
    if len(uname_clean) == 1:
        score += 30
        reasons.append('+30 за длину 1 символ')
    elif len(uname_clean) == 2:
        score += 25
        reasons.append('+25 за длину 2 символа')
    elif len(uname_clean) == 3:
        score += 20
        reasons.append('+20 за длину 3 символа')
    elif len(uname_clean) <= 5:
        score += 15
        reasons.append('+15 за короткую длину')
    elif len(uname_clean) <= 8:
        score += 10
        reasons.append('+10 за среднюю длину')
    else:
        score += 5
        reasons.append('+5 за длинный юзернейм')
    
    # Only letters
    if uname_clean.isalpha():
        score += 15
        reasons.append('+15 за только буквы')
    elif uname_clean.replace('_', '').isalnum():
        score += 5
        reasons.append('+5 за буквы/цифры')
    
    # No underscores
    if '_' not in uname_clean:
        score += 10
        reasons.append('+10 за отсутствие подчёркиваний')
    
    # Uniqueness of letters
    unique_letters = len(set(uname_clean.replace('_', '')))
    total_letters = len(uname_clean.replace('_', ''))
    if total_letters > 0 and unique_letters / total_letters > 0.7:
        score += 10
        reasons.append('+10 за уникальность букв')
    
    # No double letters
    has_double = any(uname_clean[i] == uname_clean[i+1] for i in range(len(uname_clean)-1))
    if not has_double:
        score += 10
        reasons.append('+10 за отсутствие сдвоенных букв')
    
    # Vowel/consonant alternation (simple check)
    vowels = 'aeiouy'
    vowel_pattern = [c in vowels for c in uname_clean if c.isalpha()]
    if len(vowel_pattern) >= 2:
        alternation = sum(1 for i in range(len(vowel_pattern)-1) if vowel_pattern[i] != vowel_pattern[i+1])
        if alternation >= len(vowel_pattern) - 2:
            score += 10
            reasons.append('+10 за хорошую произносимость')
    
    if score > 100:
        score = 100
    if score < 0:
        score = 0
    
    return score, reasons

def get_username_rarity(score, uname):
    uname_clean = uname.lower()
    if uname_clean == '67':
        return '67'
    if uname_clean in LEGENDARY_USERNAMES:
        return 'legend'
    if score >= 90:
        return 'legend'
    elif score >= 70:
        return 'myth'
    elif score >= 60:
        return 'epic'
    elif score >= 50:
        return 'rare'
    else:
        return 'common'

RARIETY_COLORS = {
    'common': '#808080',
    'rare': '#3399ff',
    'epic': '#9933ff',
    'myth': '#ff3333',
    'legend': '#ffd700',
    '67': '#006400'
}

RARIETY_NAMES = {
    'common': 'Обычная',
    'rare': 'Редкая',
    'epic': 'Эпическая',
    'myth': 'Мифическая',
    'legend': 'Легендарная',
    '67': '67'
}

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('search'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        login_name = request.form.get('login', '').strip()
        display_name = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not login_name or not display_name or not password:
            flash('Заполните все поля')
            return render_template('register.html')
        
        conn = get_db()
        existing = conn.execute('SELECT * FROM users WHERE login = ?', (login_name,)).fetchone()
        if existing:
            flash('Такой логин уже существует')
            conn.close()
            return render_template('register.html')
        
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cur = conn.cursor()
        cur.execute('INSERT INTO users (login, password_hash, username) VALUES (?, ?, ?)',
                    (login_name, password_hash, display_name))
        conn.commit()
        user_id = cur.lastrowid
        conn.close()
        
        session['user_id'] = user_id
        return redirect(url_for('search'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_name = request.form.get('login', '').strip()
        password = request.form.get('password', '')
        
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE login = ?', (login_name,)).fetchone()
        conn.close()
        
        if not user:
            flash('Неверный логин или пароль')
            return render_template('login.html')
        
        if user['blocked']:
            session['blocked_user_id'] = user['id']
            return redirect(url_for('blocked'))
        
        if bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            session['user_id'] = user['id']
            return redirect(url_for('search'))
        else:
            flash('Неверный логин или пароль')
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/blocked')
def blocked():
    return render_template('blocked.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/search')
@login_required
def search():
    user = get_current_user()
    conn = get_db()
    users = conn.execute('SELECT * FROM users WHERE id != ? ORDER BY username', (user['id'],)).fetchall()
    
    # Get chats
    chats = conn.execute('''SELECT pc.*, u.username as other_username, u.id as other_id, u.avatar, u.premium, u.premium_emoji, u.verified, u.is_online, u.is_admin
                           FROM private_chats pc
                           JOIN users u ON (u.id = pc.user1_id AND pc.user2_id = ?) OR (u.id = pc.user2_id AND pc.user1_id = ?)
                           WHERE pc.user1_id = ? OR pc.user2_id = ?
                           ''', (user['id'], user['id'], user['id'], user['id'])).fetchall()
    
    chat_list = []
    for chat in chats:
        other_id = chat['other_id']
        # Get last message
        last_msg = conn.execute('SELECT * FROM messages WHERE chat_id = ? ORDER BY created_at DESC LIMIT 1', (chat['id'],)).fetchone()
        # Count unread
        unread = conn.execute('SELECT COUNT(*) as cnt FROM messages WHERE chat_id = ? AND sender_id != ? AND is_read = 0', (chat['id'], user['id'])).fetchone()['cnt']
        chat_list.append({
            'chat': chat,
            'last_msg': last_msg,
            'unread': unread
        })
    
    conn.close()
    return render_template('search.html', users=users, chat_list=chat_list)

@app.route('/chat/<int:other_id>')
@login_required
def chat(other_id):
    user = get_current_user()
    conn = get_db()
    other = conn.execute('SELECT * FROM users WHERE id = ?', (other_id,)).fetchone()
    if not other:
        conn.close()
        flash('Пользователь не найден')
        return redirect(url_for('search'))
    
    # Check if blocked
    block1 = conn.execute('SELECT * FROM blocks WHERE blocker_id = ? AND blocked_id = ?', (user['id'], other_id)).fetchone()
    block2 = conn.execute('SELECT * FROM blocks WHERE blocker_id = ? AND blocked_id = ?', (other_id, user['id'])).fetchone()
    
    # Get or create chat
    pc = conn.execute('''SELECT * FROM private_chats WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)''',
                      (user['id'], other_id, other_id, user['id'])).fetchone()
    if not pc:
        cur = conn.cursor()
        cur.execute('INSERT INTO private_chats (user1_id, user2_id) VALUES (?, ?)', (user['id'], other_id))
        conn.commit()
        chat_id = cur.lastrowid
    else:
        chat_id = pc['id']
    
    messages = conn.execute('''SELECT m.*, u.username as sender_username, u.avatar as sender_avatar, u.id as sender_id
                              FROM messages m
                              JOIN users u ON u.id = m.sender_id
                              WHERE m.chat_id = ?
                              ORDER BY m.created_at ASC''', (chat_id,)).fetchall()
    
    # Mark messages as read
    conn.execute('UPDATE messages SET is_read = 1 WHERE chat_id = ? AND sender_id != ?', (chat_id, user['id']))
    conn.commit()
    
    # Get reactions for messages
    msg_reactions = {}
    for msg in messages:
        reactions = conn.execute('''SELECT r.*, u.username FROM reactions r JOIN users u ON u.id = r.user_id WHERE r.message_id = ?''', (msg['id'],)).fetchall()
        msg_reactions[msg['id']] = reactions
    
    conn.close()
    return render_template('chat.html', other=other, messages=messages, chat_id=chat_id, msg_reactions=msg_reactions, block1=block1, block2=block2)

@socketio.on('connect')
def handle_connect():
    if 'user_id' in session:
        conn = get_db()
        conn.execute('UPDATE users SET is_online = 1 WHERE id = ?', (session['user_id'],))
        conn.commit()
        conn.close()

@socketio.on('disconnect')
def handle_disconnect():
    if 'user_id' in session:
        conn = get_db()
        conn.execute('UPDATE users SET is_online = 0 WHERE id = ?', (session['user_id'],))
        conn.commit()
        conn.close()

@socketio.on('join')
def handle_join(data):
    room = data.get('room')
    if room:
        join_room(room)

@socketio.on('send_message')
def handle_send_message(data):
    if 'user_id' not in session:
        return
    user_id = session['user_id']
    chat_id = data.get('chat_id')
    content = data.get('content', '')
    reply_to = data.get('reply_to')
    
    conn = get_db()
    pc = conn.execute('SELECT * FROM private_chats WHERE id = ?', (chat_id,)).fetchone()
    if not pc:
        conn.close()
        return
    
    other_id = pc['user2_id'] if pc['user1_id'] == user_id else pc['user1_id']
    
    # Check blocks
    block1 = conn.execute('SELECT * FROM blocks WHERE blocker_id = ? AND blocked_id = ?', (user_id, other_id)).fetchone()
    block2 = conn.execute('SELECT * FROM blocks WHERE blocker_id = ? AND blocked_id = ?', (other_id, user_id)).fetchone()
    
    if block2:
        emit('error', {'msg': 'Этот пользователь заблокировал тебя'})
        conn.close()
        return
    if block1:
        emit('error', {'msg': 'Ты заблокировал этого пользователя'})
        conn.close()
        return
    
    cur = conn.cursor()
    cur.execute('INSERT INTO messages (chat_id, sender_id, content, reply_to) VALUES (?, ?, ?, ?)',
                (chat_id, user_id, content, reply_to))
    conn.commit()
    conn.close()
    
    emit('chat_updated', {'chat_id': chat_id}, room=f'chat_{chat_id}')
    join_room(f'chat_{chat_id}')

@app.route('/upload_photo', methods=['POST'])
@login_required
def upload_photo():
    user = get_current_user()
    if 'photo' not in request.files:
        flash('Файл не выбран')
        return redirect(request.referrer)
    file = request.files['photo']
    chat_id = request.form.get('chat_id')
    reply_to = request.form.get('reply_to')
    
    if file.filename == '':
        flash('Файл не выбран')
        return redirect(request.referrer)
    
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = ''.join(random.choices(string.ascii_letters + string.digits, k=32)) + '.' + ext
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        conn = get_db()
        pc = conn.execute('SELECT * FROM private_chats WHERE id = ?', (chat_id,)).fetchone()
        if pc:
            other_id = pc['user2_id'] if pc['user1_id'] == user['id'] else pc['user1_id']
            block1 = conn.execute('SELECT * FROM blocks WHERE blocker_id = ? AND blocked_id = ?', (user['id'], other_id)).fetchone()
            block2 = conn.execute('SELECT * FROM blocks WHERE blocker_id = ? AND blocked_id = ?', (other_id, user['id'])).fetchone()
            if not block1 and not block2:
                cur = conn.cursor()
                cur.execute('INSERT INTO messages (chat_id, sender_id, content, is_photo, reply_to) VALUES (?, ?, ?, 1, ?)',
                            (chat_id, user['id'], filename, reply_to))
                conn.commit()
        conn.close()
        socketio.emit('chat_updated', {'chat_id': chat_id}, room=f'chat_{chat_id}')
    
    return redirect(request.referrer)

@app.route('/send_sticker', methods=['POST'])
@login_required
def send_sticker():
    user = get_current_user()
    chat_id = request.form.get('chat_id')
    sticker = request.form.get('sticker')
    reply_to = request.form.get('reply_to')
    
    if sticker not in STICKERS:
        return redirect(request.referrer)
    
    conn = get_db()
    pc = conn.execute('SELECT * FROM private_chats WHERE id = ?', (chat_id,)).fetchone()
    if pc:
        other_id = pc['user2_id'] if pc['user1_id'] == user['id'] else pc['user1_id']
        block1 = conn.execute('SELECT * FROM blocks WHERE blocker_id = ? AND blocked_id = ?', (user['id'], other_id)).fetchone()
        block2 = conn.execute('SELECT * FROM blocks WHERE blocker_id = ? AND blocked_id = ?', (other_id, user['id'])).fetchone()
        if not block1 and not block2:
            cur = conn.cursor()
            cur.execute('INSERT INTO messages (chat_id, sender_id, content, is_sticker, reply_to) VALUES (?, ?, ?, 1, ?)',
                        (chat_id, user['id'], sticker, reply_to))
            conn.commit()
    conn.close()
    socketio.emit('chat_updated', {'chat_id': chat_id}, room=f'chat_{chat_id}')
    return redirect(request.referrer)

@app.route('/delete_message', methods=['POST'])
@login_required
def delete_message():
    user = get_current_user()
    msg_id = request.form.get('msg_id')
    conn = get_db()
    msg = conn.execute('SELECT * FROM messages WHERE id = ?', (msg_id,)).fetchone()
    if msg and msg['sender_id'] == user['id']:
        conn.execute('UPDATE messages SET is_deleted = 1, content = ? WHERE id = ?', ('сообщение удалено', msg_id))
        conn.commit()
        socketio.emit('chat_updated', {'chat_id': msg['chat_id']}, room=f'chat_{msg["chat_id"]}')
    conn.close()
    return redirect(request.referrer)

@app.route('/add_reaction', methods=['POST'])
@login_required
def add_reaction():
    user = get_current_user()
    msg_id = request.form.get('msg_id')
    reaction = request.form.get('reaction')
    chat_id = request.form.get('chat_id')
    
    # Check permissions
    if reaction in PREMIUM_REACTIONS and not user['premium']:
        flash('Только с премиумом')
        return redirect(request.referrer)
    if reaction in RARE_REACTIONS and not (user['verified'] or user['is_admin']):
        flash('Только для верифицированных и админов')
        return redirect(request.referrer)
    if reaction not in BASE_REACTIONS and reaction not in PREMIUM_REACTIONS and reaction not in RARE_REACTIONS:
        return redirect(request.referrer)
    
    conn = get_db()
    existing = conn.execute('SELECT * FROM reactions WHERE message_id = ? AND user_id = ? AND reaction = ?', (msg_id, user['id'], reaction)).fetchone()
    if existing:
        conn.execute('DELETE FROM reactions WHERE id = ?', (existing['id'],))
    else:
        conn.execute('INSERT INTO reactions (message_id, user_id, reaction) VALUES (?, ?, ?)', (msg_id, user['id'], reaction))
    conn.commit()
    conn.close()
    socketio.emit('chat_updated', {'chat_id': chat_id}, room=f'chat_{chat_id}')
    return redirect(request.referrer)

@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    user = get_current_user()
    conn = get_db()
    profile_user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not profile_user:
        conn.close()
        flash('Пользователь не найден')
        return redirect(url_for('search'))
    
    usernames = conn.execute('SELECT * FROM user_usernames WHERE user_id = ? ORDER BY created_at DESC', (user_id,)).fetchall()
    
    is_blocked = conn.execute('SELECT * FROM blocks WHERE blocker_id = ? AND blocked_id = ?', (user['id'], user_id)).fetchone()
    
    conn.close()
    return render_template('profile.html', profile_user=profile_user, usernames=usernames, is_blocked=is_blocked)

@app.route('/block_user/<int:user_id>')
@login_required
def block_user(user_id):
    user = get_current_user()
    if user_id == user['id']:
        return redirect(request.referrer)
    # Can't block admin
    conn = get_db()
    target = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if target and target['is_admin']:
        flash('Нельзя заблокировать админа')
        conn.close()
        return redirect(request.referrer)
    conn.execute('INSERT OR IGNORE INTO blocks (blocker_id, blocked_id) VALUES (?, ?)', (user['id'], user_id))
    conn.commit()
    conn.close()
    flash('Пользователь заблокирован')
    return redirect(request.referrer)

@app.route('/unblock_user/<int:user_id>')
@login_required
def unblock_user(user_id):
    user = get_current_user()
    conn = get_db()
    conn.execute('DELETE FROM blocks WHERE blocker_id = ? AND blocked_id = ?', (user['id'], user_id))
    conn.commit()
    conn.close()
    flash('Пользователь разблокирован')
    return redirect(request.referrer)

@app.route('/wallet')
@login_required
def wallet():
    user = get_current_user()
    return render_template('wallet.html', user=user)

@app.route('/buy_premium')
@login_required
def buy_premium():
    user = get_current_user()
    conn = get_db()
    if user['balance'] >= 500 and not user['premium']:
        conn.execute('UPDATE users SET balance = balance - 500, premium = 1 WHERE id = ?', (user['id'],))
        conn.commit()
        flash('Премиум куплен!')
    else:
        flash('Недостаточно зан или премиум уже активен')
    conn.close()
    return redirect(url_for('wallet'))

@app.route('/market')
@login_required
def market():
    user = get_current_user()
    conn = get_db()
    my_usernames = conn.execute('SELECT * FROM user_usernames WHERE user_id = ?', (user['id'],)).fetchall()
    for_sale = conn.execute('''SELECT uu.*, u.username as owner_name FROM user_usernames uu JOIN users u ON u.id = uu.user_id WHERE uu.for_sale = 1 AND uu.user_id != ?''', (user['id'],)).fetchall()
    conn.close()
    return render_template('market.html', user=user, my_usernames=my_usernames, for_sale=for_sale, market_themes=MARKET_THEMES, premium_emojis=PREMIUM_EMOJIS_MARKET)

@app.route('/nft', methods=['POST'])
@login_required
def nft():
    user = get_current_user()
    uname_id = request.form.get('uname_id')
    conn = get_db()
    uname = conn.execute('SELECT * FROM user_usernames WHERE id = ? AND user_id = ?', (uname_id, user['id'])).fetchone()
    if not uname:
        conn.close()
        return redirect(url_for('market'))
    
    if uname['is_nft']:
        conn.close()
        return redirect(url_for('market'))
    
    if user['free_nft_used'] == 0:
        # First free
        conn.execute('UPDATE user_usernames SET is_nft = 1 WHERE id = ?', (uname_id,))
        conn.execute('UPDATE users SET free_nft_used = 1 WHERE id = ?', (user['id'],))
        flash('NFT создан бесплатно!')
    else:
        price = max(100, uname['score'] * 10)
        if user['balance'] >= price:
            conn.execute('UPDATE users SET balance = balance - ? WHERE id = ?', (price, user['id']))
            conn.execute('UPDATE user_usernames SET is_nft = 1 WHERE id = ?', (uname_id,))
            flash(f'NFT создан за {price} зан')
        else:
            flash('Недостаточно зан')
    conn.commit()
    conn.close()
    return redirect(url_for('market'))

@app.route('/market_sell', methods=['POST'])
@login_required
def market_sell():
    user = get_current_user()
    uname_id = request.form.get('uname_id')
    price = int(request.form.get('price', 0))
    conn = get_db()
    uname = conn.execute('SELECT * FROM user_usernames WHERE id = ? AND user_id = ? AND is_nft = 1', (uname_id, user['id'])).fetchone()
    if uname and price >= 0:
        conn.execute('UPDATE user_usernames SET for_sale = 1, sale_price = ? WHERE id = ?', (price, uname_id))
        flash('Юз выставлен на продажу')
    conn.commit()
    conn.close()
    return redirect(url_for('market'))

@app.route('/market_unsell', methods=['POST'])
@login_required
def market_unsell():
    user = get_current_user()
    uname_id = request.form.get('uname_id')
    conn = get_db()
    conn.execute('UPDATE user_usernames SET for_sale = 0 WHERE id = ? AND user_id = ?', (uname_id, user['id']))
    conn.commit()
    conn.close()
    return redirect(url_for('market'))

@app.route('/market_buy_uname', methods=['POST'])
@login_required
def market_buy_uname():
    user = get_current_user()
    uname_id = request.form.get('uname_id')
    conn = get_db()
    uname = conn.execute('SELECT * FROM user_usernames WHERE id = ? AND for_sale = 1', (uname_id,)).fetchone()
    if not uname:
        conn.close()
        return redirect(url_for('market'))
    if uname['user_id'] == user['id']:
        conn.close()
        return redirect(url_for('market'))
    if user['balance'] < uname['sale_price']:
        flash('Недостаточно зан')
        conn.close()
        return redirect(url_for('market'))
    
    # Transfer
    conn.execute('UPDATE users SET balance = balance - ? WHERE id = ?', (uname['sale_price'], user['id']))
    conn.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (uname['sale_price'], uname['user_id']))
    conn.execute('UPDATE user_usernames SET user_id = ?, for_sale = 0 WHERE id = ?', (user['id'], uname_id))
    conn.commit()
    conn.close()
    flash('Юз куплен!')
    return redirect(url_for('market'))

@app.route('/market_buy_theme', methods=['POST'])
@login_required
def market_buy_theme():
    user = get_current_user()
    theme_key = request.form.get('theme_key')
    if theme_key not in MARKET_THEMES:
        return redirect(url_for('market'))
    conn = get_db()
    owned = user['owned_themes'].split(',') if user['owned_themes'] else []
    if theme_key in owned:
        flash('Уже куплено')
        conn.close()
        return redirect(url_for('market'))
    price = MARKET_THEMES[theme_key]['price']
    if user['balance'] < price:
        flash('Недостаточно зан')
        conn.close()
        return redirect(url_for('market'))
    owned.append(theme_key)
    conn.execute('UPDATE users SET balance = balance - ?, owned_themes = ? WHERE id = ?', (price, ','.join([x for x in owned if x]), user['id']))
    conn.commit()
    conn.close()
    flash('Тема куплена!')
    return redirect(url_for('market'))

@app.route('/market_buy_emoji', methods=['POST'])
@login_required
def market_buy_emoji():
    user = get_current_user()
    emoji = request.form.get('emoji')
    if emoji not in PREMIUM_EMOJIS_MARKET:
        return redirect(url_for('market'))
    conn = get_db()
    owned = user['owned_emojis'].split(',') if user['owned_emojis'] else []
    if emoji in owned:
        flash('Уже куплено')
        conn.close()
        return redirect(url_for('market'))
    price = PREMIUM_EMOJIS_MARKET[emoji]
    if user['balance'] < price:
        flash('Недостаточно зан')
        conn.close()
        return redirect(url_for('market'))
    owned.append(emoji)
    conn.execute('UPDATE users SET balance = balance - ?, owned_emojis = ? WHERE id = ?', (price, ','.join([x for x in owned if x]), user['id']))
    conn.commit()
    conn.close()
    flash('Эмодзи куплено!')
    return redirect(url_for('market'))

@app.route('/market_buy_premium')
@login_required
def market_buy_premium():
    return buy_premium()

import json

@app.route('/settings')
@login_required
def settings():
    user = get_current_user()
    conn = get_db()
    my_usernames = conn.execute('SELECT * FROM user_usernames WHERE user_id = ?', (user['id'],)).fetchall()
    owned = user['owned_themes'].split(',') if user['owned_themes'] else []
    owned_emojis = user['owned_emojis'].split(',') if user['owned_emojis'] else []
    conn.close()
    # Build theme preview data
    preview_themes = {}
    for k, v in THEMES.items():
        preview_themes[k] = v
    for k, mt in MARKET_THEMES.items():
        base = THEMES['default'].copy()
        base.update(mt.get('theme', {}))
        base['name'] = mt['name']
        preview_themes[k] = base
    return render_template('settings.html', user=user, my_usernames=my_usernames, owned_themes=owned, owned_emojis=owned_emojis, all_themes=THEMES, premium_themes=PREMIUM_THEMES, market_themes=MARKET_THEMES, preview_themes_json=json.dumps(preview_themes, ensure_ascii=False))

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    user = get_current_user()
    username = request.form.get('username', user['username']).strip()
    bio = request.form.get('bio', user['bio'] if user['bio'] else '').strip()
    # Preserve theme if not explicitly submitted
    if 'theme' in request.form and request.form.get('theme'):
        theme = request.form.get('theme')
    else:
        theme = user['theme'] if user['theme'] else 'default'
    if 'premium_emoji' in request.form:
        premium_emoji = request.form.get('premium_emoji', '')
    else:
        premium_emoji = user['premium_emoji'] if user['premium_emoji'] else ''
    
    conn = get_db()
    # Check theme
    if theme in PREMIUM_THEMES and not user['premium']:
        flash('Премиум тема недоступна')
        conn.close()
        return redirect(url_for('settings'))
    owned = user['owned_themes'].split(',') if user['owned_themes'] else []
    if theme in MARKET_THEMES and theme not in owned:
        flash('Тема не куплена')
        conn.close()
        return redirect(url_for('settings'))
    # Allow market themes that exist in THEMES? market themes stored separately but we need to support them
    # Check if theme is valid
    valid_theme = theme in THEMES or theme in MARKET_THEMES or theme in owned
    if not valid_theme and theme != 'default':
        theme = user['theme'] if user['theme'] else 'default'
    
    conn.execute('UPDATE users SET username = ?, bio = ?, theme = ?, premium_emoji = ? WHERE id = ?', (username, bio, theme, premium_emoji, user['id']))
    conn.commit()
    conn.close()
    flash('Профиль обновлён')
    return redirect(url_for('settings'))

@app.route('/upload_avatar', methods=['POST'])
@login_required
def upload_avatar():
    user = get_current_user()
    if 'avatar' not in request.files:
        return redirect(url_for('settings'))
    file = request.files['avatar']
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = 'avatar_' + ''.join(random.choices(string.ascii_letters + string.digits, k=24)) + '.' + ext
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        conn = get_db()
        conn.execute('UPDATE users SET avatar = ? WHERE id = ?', (filename, user['id']))
        conn.commit()
        conn.close()
        flash('Аватар обновлён')
    return redirect(url_for('settings'))

@app.route('/upload_banner', methods=['POST'])
@login_required
def upload_banner():
    user = get_current_user()
    if not user['premium']:
        flash('Баннер только с премиумом')
        return redirect(url_for('settings'))
    if 'banner' not in request.files:
        return redirect(url_for('settings'))
    file = request.files['banner']
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = 'banner_' + ''.join(random.choices(string.ascii_letters + string.digits, k=24)) + '.' + ext
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        conn = get_db()
        conn.execute('UPDATE users SET banner = ? WHERE id = ?', (filename, user['id']))
        conn.commit()
        conn.close()
        flash('Баннер обновлён')
    return redirect(url_for('settings'))

@app.route('/check_username', methods=['POST'])
@login_required
def check_username():
    user = get_current_user()
    uname = request.form.get('uname', '').strip().lstrip('@')
    
    if len(uname) == 0:
        return jsonify({'error': 'Пустой юзернейм'})
    
    # Check if only latin letters, numbers, underscore
    import re
    if not re.match(r'^[a-zA-Z0-9_]+$', uname):
        return jsonify({'error': 'Только латиница, цифры, подчёркивания'})
    
    conn = get_db()
    existing = conn.execute('SELECT * FROM user_usernames WHERE uname = ?', (uname.lower(),)).fetchone()
    if existing:
        conn.close()
        return jsonify({'error': 'Юзернейм уже занят'})
    
    # Count user's usernames
    count = conn.execute('SELECT COUNT(*) as cnt FROM user_usernames WHERE user_id = ?', (user['id'],)).fetchone()['cnt']
    if count >= 5:
        conn.close()
        return jsonify({'error': 'Максимум 5 юзернеймов'})
    
    score, reasons = calculate_username_score(uname)
    rarity = get_username_rarity(score, uname)
    
    conn.close()
    return jsonify({
        'uname': uname,
        'score': score,
        'reasons': reasons,
        'rarity': rarity,
        'rarity_name': RARIETY_NAMES[rarity],
        'rarity_color': RARIETY_COLORS[rarity]
    })

@app.route('/confirm_username', methods=['POST'])
@login_required
def confirm_username():
    user = get_current_user()
    uname = request.form.get('uname', '').strip().lstrip('@')
    
    import re
    if not re.match(r'^[a-zA-Z0-9_]+$', uname):
        flash('Неверный формат')
        return redirect(url_for('settings'))
    
    conn = get_db()
    existing = conn.execute('SELECT * FROM user_usernames WHERE uname = ?', (uname.lower(),)).fetchone()
    if existing:
        conn.close()
        flash('Юзернейм уже занят')
        return redirect(url_for('settings'))
    
    count = conn.execute('SELECT COUNT(*) as cnt FROM user_usernames WHERE user_id = ?', (user['id'],)).fetchone()['cnt']
    if count >= 5:
        conn.close()
        flash('Максимум 5 юзернеймов')
        return redirect(url_for('settings'))
    
    score, reasons = calculate_username_score(uname)
    rarity = get_username_rarity(score, uname)
    reason_str = '; '.join(reasons)
    
    cur = conn.cursor()
    cur.execute('INSERT INTO user_usernames (user_id, uname, score, reason, rarity) VALUES (?, ?, ?, ?, ?)',
                (user['id'], uname.lower(), score, reason_str, rarity))
    
    # Check if it's banan - give superadmin
    if uname.lower() == 'banan':
        cur.execute('UPDATE users SET is_admin = 1 WHERE id = ?', (user['id'],))
        flash('Ты получил права суперадмина!')
    
    conn.commit()
    conn.close()
    flash('Юзернейм создан!')
    return redirect(url_for('settings'))

@app.route('/cancel_username')
@login_required
def cancel_username():
    return redirect(url_for('settings'))

@app.route('/delete_username', methods=['POST'])
@login_required
def delete_username():
    user = get_current_user()
    uname_id = request.form.get('uname_id')
    conn = get_db()
    uname = conn.execute('SELECT * FROM user_usernames WHERE id = ? AND user_id = ?', (uname_id, user['id'])).fetchone()
    if uname:
        if uname['uname'] == 'banan':
            conn.execute('UPDATE users SET is_admin = 0 WHERE id = ?', (user['id'],))
        conn.execute('DELETE FROM user_usernames WHERE id = ?', (uname_id,))
        flash('Юзернейм удалён')
    conn.commit()
    conn.close()
    return redirect(url_for('settings'))

@app.route('/delete_my_account', methods=['POST'])
@login_required
def delete_my_account():
    user = get_current_user()
    conn = get_db()
    # Delete all chats, messages, reactions, etc.
    # Get all chats
    chats = conn.execute('SELECT * FROM private_chats WHERE user1_id = ? OR user2_id = ?', (user['id'], user['id'])).fetchall()
    for chat in chats:
        conn.execute('DELETE FROM messages WHERE chat_id = ?', (chat['id'],))
        conn.execute('DELETE FROM private_chats WHERE id = ?', (chat['id'],))
    conn.execute('DELETE FROM reactions WHERE user_id = ?', (user['id'],))
    conn.execute('DELETE FROM user_usernames WHERE user_id = ?', (user['id'],))
    conn.execute('DELETE FROM blocks WHERE blocker_id = ? OR blocked_id = ?', (user['id'], user['id']))
    conn.execute('DELETE FROM users WHERE id = ?', (user['id'],))
    conn.commit()
    conn.close()
    session.clear()
    flash('Аккаунт удалён')
    return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin():
    user = get_current_user()
    if not user['is_admin']:
        flash('Панель только для суперадмина')
        return redirect(url_for('search'))
    
    conn = get_db()
    users = conn.execute('SELECT * FROM users ORDER BY id').fetchall()
    all_usernames = {}
    for u in users:
        unames = conn.execute('SELECT * FROM user_usernames WHERE user_id = ?', (u['id'],)).fetchall()
        all_usernames[u['id']] = unames
    conn.close()
    return render_template('admin.html', users=users, all_usernames=all_usernames, rarities=RARIETY_NAMES)

@app.route('/admin_give', methods=['POST'])
@login_required
def admin_give():
    user = get_current_user()
    if not user['is_admin']:
        return redirect(url_for('search'))
    target_id = request.form.get('target_id')
    amount = int(request.form.get('amount', 0))
    conn = get_db()
    conn.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (amount, target_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/admin_take', methods=['POST'])
@login_required
def admin_take():
    user = get_current_user()
    if not user['is_admin']:
        return redirect(url_for('search'))
    target_id = request.form.get('target_id')
    amount = int(request.form.get('amount', 0))
    conn = get_db()
    conn.execute('UPDATE users SET balance = balance - ? WHERE id = ?', (amount, target_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/admin_double', methods=['POST'])
@login_required
def admin_double():
    user = get_current_user()
    if not user['is_admin']:
        return redirect(url_for('search'))
    target_id = request.form.get('target_id')
    conn = get_db()
    target = conn.execute('SELECT balance FROM users WHERE id = ?', (target_id,)).fetchone()
    if target:
        conn.execute('UPDATE users SET balance = ? WHERE id = ?', (target['balance'] * 2, target_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/admin_premium', methods=['POST'])
@login_required
def admin_premium():
    user = get_current_user()
    if not user['is_admin']:
        return redirect(url_for('search'))
    target_id = request.form.get('target_id')
    conn = get_db()
    target = conn.execute('SELECT premium FROM users WHERE id = ?', (target_id,)).fetchone()
    if target:
        new_prem = 0 if target['premium'] else 1
        conn.execute('UPDATE users SET premium = ? WHERE id = ?', (new_prem, target_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/admin_verify', methods=['POST'])
@login_required
def admin_verify():
    user = get_current_user()
    if not user['is_admin']:
        return redirect(url_for('search'))
    target_id = request.form.get('target_id')
    conn = get_db()
    target = conn.execute('SELECT verified FROM users WHERE id = ?', (target_id,)).fetchone()
    if target:
        new_ver = 0 if target['verified'] else 1
        conn.execute('UPDATE users SET verified = ? WHERE id = ?', (new_ver, target_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/admin_block', methods=['POST'])
@login_required
def admin_block():
    user = get_current_user()
    if not user['is_admin']:
        return redirect(url_for('search'))
    target_id = request.form.get('target_id')
    conn = get_db()
    target = conn.execute('SELECT blocked, is_admin FROM users WHERE id = ?', (target_id,)).fetchone()
    if target and target['is_admin'] and target_id != user['id']:
        flash('Нельзя заблокировать другого админа')
        conn.close()
        return redirect(url_for('admin'))
    if target:
        new_block = 0 if target['blocked'] else 1
        conn.execute('UPDATE users SET blocked = ? WHERE id = ?', (new_block, target_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/admin_set_rarity', methods=['POST'])
@login_required
def admin_set_rarity():
    user = get_current_user()
    if not user['is_admin']:
        return redirect(url_for('search'))
    uname_id = request.form.get('uname_id')
    rarity = request.form.get('rarity')
    conn = get_db()
    conn.execute('UPDATE user_usernames SET rarity = ? WHERE id = ?', (rarity, uname_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/admin_delete_uname', methods=['POST'])
@login_required
def admin_delete_uname():
    user = get_current_user()
    if not user['is_admin']:
        return redirect(url_for('search'))
    uname_id = request.form.get('uname_id')
    conn = get_db()
    uname = conn.execute('SELECT uname, user_id FROM user_usernames WHERE id = ?', (uname_id,)).fetchone()
    if uname and uname['uname'] == 'banan':
        conn.execute('UPDATE users SET is_admin = 0 WHERE id = ?', (uname['user_id'],))
    conn.execute('DELETE FROM user_usernames WHERE id = ?', (uname_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/admin_delete_account', methods=['POST'])
@login_required
def admin_delete_account():
    user = get_current_user()
    if not user['is_admin']:
        return redirect(url_for('search'))
    target_id = request.form.get('target_id')
    if int(target_id) == user['id']:
        flash('Нельзя удалить себя')
        return redirect(url_for('admin'))
    conn = get_db()
    target = conn.execute('SELECT is_admin FROM users WHERE id = ?', (target_id,)).fetchone()
    if target and target['is_admin']:
        flash('Нельзя удалить другого админа')
        conn.close()
        return redirect(url_for('admin'))
    
    chats = conn.execute('SELECT * FROM private_chats WHERE user1_id = ? OR user2_id = ?', (target_id, target_id)).fetchall()
    for chat in chats:
        conn.execute('DELETE FROM messages WHERE chat_id = ?', (chat['id'],))
        conn.execute('DELETE FROM private_chats WHERE id = ?', (chat['id'],))
    conn.execute('DELETE FROM reactions WHERE user_id = ?', (target_id,))
    conn.execute('DELETE FROM user_usernames WHERE user_id = ?', (target_id,))
    conn.execute('DELETE FROM blocks WHERE blocker_id = ? OR blocked_id = ?', (target_id, target_id))
    conn.execute('DELETE FROM users WHERE id = ?', (target_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("DEBUG", "False").lower() == "true"
    socketio.run(app, debug=debug, host='0.0.0.0', port=port)
