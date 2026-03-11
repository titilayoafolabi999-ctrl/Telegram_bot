#!/usr/bin/env python3
"""
Full-featured Telegram bot with:
- Gemini integration (text generation)
- Context memory, personalities
- Rate limiting, moderation (profanity + optional Perspective)
- Credits, daily check-in, referrals
- Reminders (scheduler)
- Admin runtime env management and token rotation (store tokens)
- User -> Admin contact and feedback reporting; admin replies
- SQLite persistence (single-instance)
"""

import os
import logging
import sqlite3
import time
import secrets
import asyncio
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple, List

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from gtts import gTTS
from telegram import Update, ChatAction, InputFile
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes
)
import google.generativeai as genai
from better_profanity import profanity

# ---------------------------
# Configuration (env + defaults)
# ---------------------------
# Required (must set)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")  # active token (protected)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Optional / defaults
PERSPECTIVE_API_KEY = os.getenv("PERSPECTIVE_API_KEY", "")  # optional toxicity API
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]  # comma-separated
DAILY_DIGEST_HOUR = int(os.getenv("DAILY_DIGEST_HOUR", "8"))  # UTC hour for daily report
RATE_LIMIT_SECONDS = int(os.getenv("RATE_LIMIT_SECONDS", "3"))
DAILY_CREDITS = int(os.getenv("DAILY_CREDITS", "10"))
CREDIT_COST_PER_MESSAGE = int(os.getenv("CREDIT_COST_PER_MESSAGE", "1"))
REFERRAL_REWARD = int(os.getenv("REFERRAL_REWARD", "5"))
DB_PATH = os.getenv("DATABASE_PATH", "bot_data.sqlite")
ALLOW_TOKEN_ROTATION = os.getenv("ALLOW_TOKEN_ROTATION", "true").lower() in ("1", "true", "yes")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=LOG_LEVEL)
logger = logging.getLogger(__name__)

# ---------------------------
# Gemini setup
# ---------------------------
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# ---------------------------
# Profanity init
# ---------------------------
profanity.load_censor_words()

# ---------------------------
# Scheduler
# ---------------------------
scheduler = BackgroundScheduler()
scheduler.start()

# ---------------------------
# Database initialization
# ---------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # memory, reminders, user_state, credits, referrals, moderation_log
    c.execute('''
        CREATE TABLE IF NOT EXISTS memory (
            user_id INTEGER,
            key TEXT,
            value TEXT,
            updated_at TIMESTAMP,
            PRIMARY KEY (user_id, key)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            chat_id INTEGER,
            text TEXT,
            remind_at TIMESTAMP,
            created_at TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_state (
            user_id INTEGER PRIMARY KEY,
            mode TEXT,
            last_context TEXT,
            last_interaction TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS credits (
            user_id INTEGER PRIMARY KEY,
            credits INTEGER,
            last_checkin TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS referrals (
            code TEXT PRIMARY KEY,
            referrer_id INTEGER,
            claimed_by INTEGER,
            created_at TIMESTAMP,
            claimed_at TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS moderation_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT,
            reason TEXT,
            severity REAL,
            created_at TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS env_vars (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS tg_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT,
            label TEXT,
            created_at TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            chat_id INTEGER,
            message TEXT,
            created_at TIMESTAMP,
            handled INTEGER DEFAULT 0
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT,
            created_at TIMESTAMP,
            handled INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ---------------------------
# Globals and rate limiting
# ---------------------------
last_message_time: Dict[int, float] = {}
globals()['APPLICATION'] = None  # will be set in main

# ---------------------------
# DB helper functions
# ---------------------------
def db_execute(query: str, params: tuple = (), fetch: bool = False):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(query, params)
    if fetch:
        rows = c.fetchall()
        conn.commit()
        conn.close()
        return rows
    conn.commit()
    conn.close()
    return None

# Memory
def set_memory(user_id: int, key: str, value: str):
    db_execute('''
        INSERT INTO memory (user_id, key, value, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
    ''', (user_id, key, value, datetime.utcnow()))

def get_memory(user_id: int, key: str) -> Optional[str]:
    rows = db_execute('SELECT value FROM memory WHERE user_id=? AND key=?', (user_id, key), fetch=True)
    return rows[0][0] if rows else None

# User state
def set_user_mode(user_id: int, mode: str):
    db_execute('''
        INSERT INTO user_state (user_id, mode, last_context, last_interaction)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET mode=excluded.mode, last_interaction=excluded.last_interaction
    ''', (user_id, mode, "", datetime.utcnow()))

def get_user_mode(user_id: int) -> str:
    rows = db_execute('SELECT mode FROM user_state WHERE user_id=?', (user_id,), fetch=True)
    return rows[0][0] if rows and rows[0][0] else "default"

def append_user_context(user_id: int, text: str, max_len=2000):
    rows = db_execute('SELECT last_context FROM user_state WHERE user_id=?', (user_id,), fetch=True)
    current = rows[0][0] if rows and rows[0][0] else ""
    new = (current + "\n" + text)[-max_len:]
    db_execute('''
        INSERT INTO user_state (user_id, mode, last_context, last_interaction)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET last_context=excluded.last_context, last_interaction=excluded.last_interaction
    ''', (user_id, get_user_mode(user_id), new, datetime.utcnow()))

def get_user_context(user_id: int) -> str:
    rows = db_execute('SELECT last_context FROM user_state WHERE user_id=?', (user_id,), fetch=True)
    return rows[0][0] if rows and rows[0][0] else ""

# Credits
def ensure_user_credits(user_id: int):
    rows = db_execute('SELECT credits FROM credits WHERE user_id=?', (user_id,), fetch=True)
    if not rows:
        db_execute('INSERT INTO credits (user_id, credits, last_checkin) VALUES (?, ?, ?)', (user_id, 0, None))

def get_credits(user_id: int) -> int:
    ensure_user_credits(user_id)
    rows = db_execute('SELECT credits FROM credits WHERE user_id=?', (user_id,), fetch=True)
    return int(rows[0][0]) if rows else 0

def add_credits(user_id: int, amount: int):
    ensure_user_credits(user_id)
    db_execute('UPDATE credits SET credits = credits + ? WHERE user_id=?', (amount, user_id))

def set_credits(user_id: int, amount: int):
    ensure_user_credits(user_id)
    db_execute('UPDATE credits SET credits = ? WHERE user_id=?', (amount, user_id))

def consume_credits(user_id: int, amount: int) -> bool:
    ensure_user_credits(user_id)
    rows = db_execute('SELECT credits FROM credits WHERE user_id=?', (user_id,), fetch=True)
    current = int(rows[0][0]) if rows else 0
    if current < amount:
        return False
    db_execute('UPDATE credits SET credits = credits - ? WHERE user_id=?', (amount, user_id))
    return True

def set_last_checkin(user_id: int, ts: datetime):
    db_execute('UPDATE credits SET last_checkin = ? WHERE user_id=?', (ts.isoformat(), user_id))

def get_last_checkin(user_id: int) -> Optional[datetime]:
    rows = db_execute('SELECT last_checkin FROM credits WHERE user_id=?', (user_id,), fetch=True)
    if rows and rows[0][0]:
        try:
            return datetime.fromisoformat(rows[0][0])
        except Exception:
            return None
    return None

# Referrals
def create_referral(referrer_id: int) -> str:
    code = secrets.token_urlsafe(8)
    db_execute('INSERT INTO referrals (code, referrer_id, claimed_by, created_at) VALUES (?, ?, ?, ?)',
               (code, referrer_id, None, datetime.utcnow()))
    return code

def claim_referral(code: str, claimer_id: int) -> Optional[int]:
    rows = db_execute('SELECT referrer_id, claimed_by FROM referrals WHERE code=?', (code,), fetch=True)
    if not rows:
        return None
    referrer_id, claimed_by = rows[0]
    if claimed_by is not None:
        return None
    db_execute('UPDATE referrals SET claimed_by=?, claimed_at=? WHERE code=?', (claimer_id, datetime.utcnow(), code))
    return referrer_id

# Moderation
def log_moderation(user_id: int, message: str, reason: str, severity: float):
    db_execute('INSERT INTO moderation_log (user_id, message, reason, severity, created_at) VALUES (?, ?, ?, ?, ?)',
               (user_id, message, reason, severity, datetime.utcnow()))

# Env vars and tokens
def set_runtime_env(key: str, value: str):
    db_execute('''
        INSERT INTO env_vars (key, value, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
    ''', (key, value, datetime.utcnow()))

def get_runtime_env(key: str) -> Optional[str]:
    rows = db_execute('SELECT value FROM env_vars WHERE key=?', (key,), fetch=True)
    return rows[0][0] if rows else None

def delete_runtime_env(key: str):
    db_execute('DELETE FROM env_vars WHERE key=?', (key,))

def list_runtime_envs() -> Dict[str, str]:
    rows = db_execute('SELECT key, value FROM env_vars', (), fetch=True)
    return {k: v for k, v in rows} if rows else {}

def add_tg_token(token: str, label: Optional[str] = None) -> int:
    db_execute('INSERT INTO tg_tokens (token, label, created_at) VALUES (?, ?, ?)', (token, label or "", datetime.utcnow()))
    rows = db_execute('SELECT last_insert_rowid()', (), fetch=True)
    # sqlite lastrowid retrieval fallback
    conn = sqlite3.connect(DB_PATH)
    tid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.close()
    return tid

def list_tg_tokens() -> List[Tuple[int, str, str]]:
    rows = db_execute('SELECT id, label, created_at FROM tg_tokens', (), fetch=True)
    return rows or []

def get_tg_token_by_id(tid: int) -> Optional[str]:
    rows = db_execute('SELECT token FROM tg_tokens WHERE id=?', (tid,), fetch=True)
    return rows[0][0] if rows else None

# User messages and feedback
def store_user_message(user_id: int, chat_id: int, message: str):
    db_execute('INSERT INTO user_messages (user_id, chat_id, message, created_at, handled) VALUES (?, ?, ?, ?, ?)',
               (user_id, chat_id, message, datetime.utcnow(), 0))

def fetch_unhandled_messages() -> List[Tuple[int, int, str, str]]:
    rows = db_execute('SELECT id, user_id, chat_id, message, created_at FROM user_messages WHERE handled=0 ORDER BY created_at ASC', (), fetch=True)
    return rows or []

def mark_message_handled(mid: int):
    db_execute('UPDATE user_messages SET handled=1 WHERE id=?', (mid,))

def store_feedback(user_id: int, message: str):
    db_execute('INSERT INTO feedback (user_id, message, created_at, handled) VALUES (?, ?, ?, ?)', (user_id, message, datetime.utcnow(), 0))

def fetch_unhandled_feedback() -> List[Tuple[int, int, str, str]]:
    rows = db_execute('SELECT id, user_id, message, created_at FROM feedback WHERE handled=0 ORDER BY created_at ASC', (), fetch=True)
    return rows or []

def mark_feedback_handled(fid: int):
    db_execute('UPDATE feedback SET handled=1 WHERE id=?', (fid,))

# Reminders
def add_reminder(user_id: int, chat_id: int, text: str, remind_at: datetime):
    db_execute('INSERT INTO reminders (user_id, chat_id, text, remind_at, created_at) VALUES (?, ?, ?, ?, ?)',
               (user_id, chat_id, text, remind_at, datetime.utcnow()))
    # schedule job
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT last_insert_rowid()')
    reminder_id = c.fetchone()[0]
    conn.close()
    scheduler.add_job(func=send_reminder_job, trigger='date', run_date=remind_at, args=[reminder_id], id=f"reminder_{reminder_id}")
    return reminder_id

def get_reminder(reminder_id: int):
    rows = db_execute('SELECT user_id, chat_id, text, remind_at FROM reminders WHERE id=?', (reminder_id,), fetch=True)
    return rows[0] if rows else None

def send_reminder_job(reminder_id: int):
    row = get_reminder(reminder_id)
    if not row:
        return
    user_id, chat_id, text, remind_at = row
    app = globals().get('APPLICATION')
    if app:
        async def _send():
            try:
                await app.bot.send_message(chat_id=chat_id, text=f"⏰ Reminder: {text}")
            except Exception as e:
                logger.error("Failed to send reminder: %s", e)
        asyncio.run(_send())

# ---------------------------
# Moderation helpers
# ---------------------------
def perspective_toxicity_score(text: str) -> Optional[float]:
    if not PERSPECTIVE_API_KEY:
        return None
    try:
        url = "https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze"
        payload = {"comment": {"text": text}, "languages": ["en"], "requestedAttributes": {"TOXICITY": {}}}
        params = {"key": PERSPECTIVE_API_KEY}
        r = requests.post(url, json=payload, params=params, timeout=6)
        if r.status_code == 200:
            data = r.json()
            score = data["attributeScores"]["TOXICITY"]["summaryScore"]["value"]
            return float(score)
    except Exception as e:
        logger.warning("Perspective API failed: %s", e)
    return None

def moderate_message(user_id: int, text: str) -> Tuple[bool, str]:
    # profanity
    if profanity.contains_profanity(text):
        log_moderation(user_id, text, "profanity", 1.0)
        return True, "Message blocked: profanity detected."
    # perspective
    score = perspective_toxicity_score(text)
    if score is not None:
        log_moderation(user_id, text, "toxicity_check", score)
        if score >= 0.85:
            return True, "Message blocked: high toxicity detected."
        if score >= 0.6:
            return False, f"Warning: message may be toxic (score {score:.2f})."
    # spam heuristics
    if len(text) > 5000:
        log_moderation(user_id, text, "too_long", 0.5)
        return True, "Message blocked: too long."
    if text.count("http://") + text.count("https://") > 5:
        log_moderation(user_id, text, "link_spam", 0.7)
        return True, "Message blocked: too many links."
    return False, ""

# ---------------------------
# Utilities: wiki, tts
# ---------------------------
def wiki_summary(query: str) -> Optional[str]:
    try:
        url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + requests.utils.requote_uri(query)
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            data = r.json()
            return data.get("extract")
    except Exception as e:
        logger.warning("Wiki lookup failed: %s", e)
    return None

def text_to_speech(text: str, lang: str = "en") -> Optional[str]:
    try:
        tts = gTTS(text=text, lang=lang)
        filename = f"tts_{int(time.time())}.mp3"
        tts.save(filename)
        return filename
    except Exception as e:
        logger.error("TTS failed: %s", e)
        return None

# ---------------------------
# Bot command handlers
# ---------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(f"Hi {user.mention_html()}! I'm a Gemini-powered assistant. Use /help to see commands.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "/start - Start\n"
        "/help - This message\n"
        "/setmode <mode> - Set personality (default,tutor,coach,funny)\n"
        "/remember <key> <value> - Save memory\n"
        "/recall <key> - Recall memory\n"
        "/remindme <minutes> <text> - Set reminder\n"
        "/search <term> - Wikipedia summary\n"
        "/tts <text> - Get voice reply\n"
        "/checkin - Claim daily credits\n"
        "/credits - Show credits\n"
        "/refer - Generate referral code\n"
        "/claimref <code> - Claim referral\n"
        "/contact_admin <message> - Send message to admins\n"
        "/feedback <message> - Send feedback to admins\n"
    )
    await update.message.reply_text(help_text)

# setmode, remember, recall
async def setmode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /setmode <default|tutor|coach|funny>")
        return
    mode = context.args[0].lower()
    if mode not in ("default", "tutor", "coach", "funny"):
        await update.message.reply_text("Unknown mode. Choose default, tutor, coach, or funny.")
        return
    set_user_mode(user_id, mode)
    await update.message.reply_text(f"Mode set to {mode}.")

async def remember(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /remember <key> <value>")
        return
    key = context.args[0]
    value = " ".join(context.args[1:])
    set_memory(user_id, key, value)
    await update.message.reply_text(f"Saved memory: {key} = {value}")

async def recall(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /recall <key>")
        return
    key = context.args[0]
    value = get_memory(user_id, key)
    if value:
        await update.message.reply_text(f"{key} = {value}")
    else:
        await update.message.reply_text("No memory found for that key.")

# reminders
async def remindme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /remindme <minutes> <text>")
        return
    try:
        minutes = int(context.args[0])
    except ValueError:
        await update.message.reply_text("First argument must be minutes (integer).")
        return
    text = " ".join(context.args[1:])
    remind_at = datetime.utcnow() + timedelta(minutes=minutes)
    reminder_id = add_reminder(user_id, chat_id, text, remind_at)
    await update.message.reply_text(f"Reminder set for {minutes} minutes from now (id {reminder_id}).")

# search and tts
async def search_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /search <term>")
        return
    term = " ".join(context.args)
    await update.message.reply_text("Searching Wikipedia...")
    summary = wiki_summary(term)
    if summary:
        await update.message.reply_text(summary)
    else:
        await update.message.reply_text("No summary found on Wikipedia.")

async def tts_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /tts <text>")
        return
    text = " ".join(context.args)
    await update.message.chat.send_action(action=ChatAction.UPLOAD_AUDIO)
    path = text_to_speech(text)
    if path:
        try:
            with open(path, "rb") as f:
                await update.message.reply_audio(audio=InputFile(f))
        finally:
            try:
                os.remove(path)
            except Exception:
                pass
    else:
        await update.message.reply_text("TTS failed.")

# credits and referrals
async def checkin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    ensure_user_credits(user_id)
    last = get_last_checkin(user_id)
    now = datetime.utcnow()
    if last and (now - last) < timedelta(hours=24):
        next_time = last + timedelta(hours=24)
        await update.message.reply_text(f"You already checked in. Next checkin available at {next_time.isoformat()} UTC.")
        return
    add_credits(user_id, DAILY_CREDITS)
    set_last_checkin(user_id, now)
    await update.message.reply_text(f"Check-in successful. You received {DAILY_CREDITS} credits. Current credits: {get_credits(user_id)}")

async def credits_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    c = get_credits(user_id)
    await update.message.reply_text(f"You have {c} credits.")

async def refer_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    code = create_referral(user_id)
    await update.message.reply_text(f"Share this referral code with a friend: {code}\nWhen they claim it, both of you get {REFERRAL_REWARD} credits.")

async def claimref_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /claimref <code>")
        return
    code = context.args[0]
    referrer = claim_referral(code, user_id)
    if not referrer:
        await update.message.reply_text("Invalid or already claimed referral code.")
        return
    add_credits(user_id, REFERRAL_REWARD)
    add_credits(referrer, REFERRAL_REWARD)
    await update.message.reply_text(f"Referral claimed. You and the referrer received {REFERRAL_REWARD} credits. Your credits: {get_credits(user_id)}")

async def leaderboard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    rows = db_execute('SELECT user_id, credits FROM credits ORDER BY credits DESC LIMIT 10', (), fetch=True)
    if not rows:
        await update.message.reply_text("No credits data yet.")
        return
    text = "Top users by credits:\n" + "\n".join(f"{uid}: {credits}" for uid, credits in rows)
    await update.message.reply_text(text)

# contact admins and feedback
async def contact_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not context.args:
        await update.message.reply_text("Usage: /contact_admin <message>")
        return
    message = " ".join(context.args)
    store_user_message(user.id, update.effective_chat.id, message)
    # notify admins
    notified = 0
    for admin in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin, text=f"📩 Message from {user.full_name} (id:{user.id}):\n{message}\nUse /inbox to view messages.")
            notified += 1
        except Exception as e:
            logger.warning("Failed to notify admin %s: %s", admin, e)
    await update.message.reply_text(f"Your message was sent to admins ({notified} notified). They can reply with /reply_user <user_id> <message>.")

async def feedback_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not context.args:
        await update.message.reply_text("Usage: /feedback <message>")
        return
    message = " ".join(context.args)
    store_feedback(user.id, message)
    # notify admins
    for admin in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin, text=f"📝 Feedback from {user.full_name} (id:{user.id}):\n{message}\nUse /feedback_inbox to view feedback.")
        except Exception:
            pass
    await update.message.reply_text("Thanks for your feedback — admins have been notified.")

# admin inbox and reply
async def inbox_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    caller = update.effective_user.id
    if caller not in ADMIN_IDS:
        await update.message.reply_text("Admin only.")
        return
    rows = fetch_unhandled_messages()
    if not rows:
        await update.message.reply_text("No unhandled user messages.")
        return
    text = "Unhandled user messages:\n"
    for r in rows:
        mid, uid, chat_id, message, created_at = r
        text += f"id:{mid} user:{uid} chat:{chat_id} at:{created_at}\n{message}\n\n"
    await update.message.reply_text(text)

async def reply_user_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    caller = update.effective_user.id
    if caller not in ADMIN_IDS:
        await update.message.reply_text("Admin only.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /reply_user <user_id> <message>")
        return
    try:
        uid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid user id.")
        return
    reply_text = " ".join(context.args[1:])
    try:
        await context.bot.send_message(chat_id=uid, text=f"Message from admin:\n{reply_text}")
        await update.message.reply_text("Reply sent.")
    except Exception as e:
        await update.message.reply_text(f"Failed to send reply: {e}")

async def mark_msg_handled_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    caller = update.effective_user.id
    if caller not in ADMIN_IDS:
        await update.message.reply_text("Admin only.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /mark_handled <message_id>")
        return
    try:
        mid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid id.")
        return
    mark_message_handled(mid)
    await update.message.reply_text(f"Marked message {mid} handled.")

# feedback inbox and reply
async def feedback_inbox_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    caller = update.effective_user.id
    if caller not in ADMIN_IDS:
        await update.message.reply_text("Admin only.")
        return
    rows = fetch_unhandled_feedback()
    if not rows:
        await update.message.reply_text("No unhandled feedback.")
        return
    text = "Unhandled feedback:\n"
    for r in rows:
        fid, uid, message, created_at = r
        text += f"id:{fid} user:{uid} at:{created_at}\n{message}\n\n"
    await update.message.reply_text(text)

async def reply_feedback_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    caller = update.effective_user.id
    if caller not in ADMIN_IDS:
        await update.message.reply_text("Admin only.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /reply_feedback <feedback_id> <message>")
        return
    try:
        fid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid feedback id.")
        return
    reply_text = " ".join(context.args[1:])
    rows = db_execute('SELECT user_id FROM feedback WHERE id=?', (fid,), fetch=True)
    if not rows:
        await update.message.reply_text("Feedback id not found.")
        return
    uid = rows[0][0]
    try:
        await context.bot.send_message(chat_id=uid, text=f"Reply from admin regarding your feedback:\n{reply_text}")
        mark_feedback_handled(fid)
        await update.message.reply_text("Reply sent and feedback marked handled.")
    except Exception as e:
        await update.message.reply_text(f"Failed to send reply: {e}")

# admin credit controls and stats
async def admin_setcredits(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    caller = update.effective_user.id
    if caller not in ADMIN_IDS:
        await update.message.reply_text("Admin only.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /setcredits <user_id> <amount>")
        return
    try:
        uid = int(context.args[0]); amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("Invalid arguments.")
        return
    set_credits(uid, amount)
    await update.message.reply_text(f"Set credits for {uid} to {amount}.")

async def admin_addcredits(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    caller = update.effective_user.id
    if caller not in ADMIN_IDS:
        await update.message.reply_text("Admin only.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /addcredits <user_id> <amount>")
        return
    try:
        uid = int(context.args[0]); amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("Invalid arguments.")
        return
    add_credits(uid, amount)
    await update.message.reply_text(f"Added {amount} credits to {uid}.")

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    caller = update.effective_user.id
    if caller not in ADMIN_IDS:
        await update.message.reply_text("Admin only.")
        return
    rows = db_execute('SELECT COUNT(*) FROM memory', (), fetch=True)
    mem_count = rows[0][0] if rows else 0
    rows = db_execute('SELECT COUNT(*) FROM reminders', (), fetch=True)
    rem_count = rows[0][0] if rows else 0
    rows = db_execute('SELECT COUNT(*) FROM referrals', (), fetch=True)
    ref_count = rows[0][0] if rows else 0
    rows = db_execute('SELECT COUNT(*) FROM moderation_log', (), fetch=True)
    mod_count = rows[0][0] if rows else 0
    await update.message.reply_text(f"Memory entries: {mem_count}\nReminders: {rem_count}\nReferrals: {ref_count}\nModeration logs: {mod_count}")

# admin env management and token store
async def admin_setenv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    caller = update.effective_user.id
    if caller not in ADMIN_IDS:
        await update.message.reply_text("Admin only.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /setenv <KEY> <VALUE>")
        return
    key = context.args[0]
    value = " ".join(context.args[1:])
    if key.upper() == "TELEGRAM_BOT_TOKEN":
        await update.message.reply_text("Cannot change active TELEGRAM_BOT_TOKEN with /setenv. Use /add_tg_token and /apply_tg_token.")
        return
    set_runtime_env(key, value)
    await update.message.reply_text(f"Set {key} = {value}")

async def admin_getenv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    caller = update.effective_user.id
    if caller not in ADMIN_IDS:
        await update.message.reply_text("Admin only.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /getenv <KEY>")
        return
    key = context.args[0]
    val = get_runtime_env(key)
    if val is None:
        await update.message.reply_text(f"{key} not set.")
    else:
        await update.message.reply_text(f"{key} = {val}")

async def admin_delenv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    caller = update.effective_user.id
    if caller not in ADMIN_IDS:
        await update.message.reply_text("Admin only.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /delenv <KEY>")
        return
    key = context.args[0]
    if key.upper() == "TELEGRAM_BOT_TOKEN":
        await update.message.reply_text("Cannot delete the active TELEGRAM_BOT_TOKEN.")
        return
    delete_runtime_env(key)
    await update.message.reply_text(f"Deleted {key} if it existed.")

async def admin_listenv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    caller = update.effective_user.id
    if caller not in ADMIN_IDS:
        await update.message.reply_text("Admin only.")
        return
    envs = list_runtime_envs()
    if not envs:
        await update.message.reply_text("No runtime env vars set.")
        return
    text = "Runtime env vars:\n" + "\n".join(f"{k}={v}" for k, v in envs.items())
    await update.message.reply_text(text)

async def admin_add_tg_token(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not ALLOW_TOKEN_ROTATION:
        await update.message.reply_text("Token rotation disabled by configuration.")
        return
    caller = update.effective_user.id
    if caller not in ADMIN_IDS:
        await update.message.reply_text("Admin only.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /add_tg_token <TOKEN> [label]")
        return
    token = context.args[0]
    label = " ".join(context.args[1:]) if len(context.args) > 1 else ""
    tid = add_tg_token(token, label)
    await update.message.reply_text(f"Stored new token id {tid}. Use /list_tg_tokens and /apply_tg_token <id> to apply.")

async def admin_list_tg_tokens(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    caller = update.effective_user.id
    if caller not in ADMIN_IDS:
        await update.message.reply_text("Admin only.")
        return
    rows = list_tg_tokens()
    if not rows:
        await update.message.reply_text("No stored tokens.")
        return
    text = "Stored tokens:\n" + "\n".join(f"id:{r[0]} label:{r[1]} created:{r[2]}" for r in rows)
    await update.message.reply_text(text)

# Token apply: attempt in-process rotation
async def admin_apply_tg_token(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not ALLOW_TOKEN_ROTATION:
        await update.message.reply_text("Token rotation disabled by configuration.")
        return
    caller = update.effective_user.id
    if caller not in ADMIN_IDS:
        await update.message.reply_text("Admin only.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /apply_tg_token <id>")
        return
    try:
        tid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid id.")
        return
    token = get_tg_token_by_id(tid)
    if not token:
        await update.message.reply_text("Token id not found.")
        return
    # persist pending token
    set_runtime_env("PENDING_TELEGRAM_BOT_TOKEN", token)
    await update.message.reply_text("Token stored as pending. Applying token now...")
    # perform in-process restart: stop current app and start new one with token
    try:
        await restart_application_with_token(token)
        await update.message.reply_text("Applied new token and restarted bot.")
    except Exception as e:
        logger.exception("Failed to apply token: %s", e)
        await update.message.reply_text(f"Failed to apply token: {e}")

# ---------------------------
# Core message handler (Gemini)
# ---------------------------
async def gemini_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    user = update.effective_user
    user_id = user.id
    text = message.text or ""
    # banned check
    banned = get_memory(user_id, "banned")
    if banned == "1":
        await message.reply_text("You are banned from using this bot.")
        return
    # rate limiting
    now = time.time()
    last = last_message_time.get(user_id, 0)
    if now - last < RATE_LIMIT_SECONDS:
        await message.reply_text("You're sending messages too quickly. Please wait a moment.")
        return
    last_message_time[user_id] = now
    # moderation
    blocked, mod_reason = moderate_message(user_id, text)
    if blocked:
        await message.reply_text(mod_reason)
        return
    elif mod_reason:
        await message.reply_text(mod_reason)
    # credits
    if not consume_credits(user_id, CREDIT_COST_PER_MESSAGE):
        await message.reply_text(
            f"You don't have enough credits. Each message costs {CREDIT_COST_PER_MESSAGE} credits.\nUse /checkin or /refer."
        )
        return
    # context
    append_user_context(user_id, f"User: {text}")
    mode = get_user_mode(user_id)
    persona_map = {
        "default": "You are a helpful assistant.",
        "tutor": "You are a patient tutor. Explain step-by-step and ask follow-ups.",
        "coach": "You are a motivational coach. Keep replies concise and encouraging.",
        "funny": "You are a witty, light-hearted companion. Keep it playful but safe."
    }
    persona = persona_map.get(mode, persona_map["default"])
    context_text = get_user_context(user_id)
    prompt = f"{persona}\nConversation history:\n{context_text}\nUser: {text}\nAssistant:"
    logger.info("Sending prompt to Gemini for user %s", user_id)
    try:
        response = model.generate_content(prompt)
        gemini_text = response.text.strip()
        append_user_context(user_id, f"Assistant: {gemini_text}")
        await message.reply_text(gemini_text)
    except Exception as e:
        logger.error("Gemini error: %s", e)
        add_credits(user_id, CREDIT_COST_PER_MESSAGE)  # refund
        await message.reply_text("Sorry, I couldn't get a response from Gemini right now. Your credits have been refunded.")

# ---------------------------
# Daily tasks and scheduling
# ---------------------------
def schedule_daily_tasks(application: Application):
    async def daily_report():
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        since = datetime.utcnow() - timedelta(days=1)
        c.execute('SELECT COUNT(*) FROM moderation_log WHERE created_at >= ?', (since,))
        mods = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM referrals WHERE created_at >= ?', (since,))
        refs = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM feedback WHERE created_at >= ?', (since,))
        fbs = c.fetchone()[0]
        conn.close()
        text = f"Daily report: moderation events: {mods}, new referrals: {refs}, new feedback: {fbs}."
        for admin in ADMIN_IDS:
            try:
                asyncio.run(application.bot.send_message(chat_id=admin, text=text))
            except Exception as e:
                logger.error("Failed to send daily report to %s: %s", admin, e)
    scheduler.add_job(func=lambda: daily_report(), trigger='cron', hour=DAILY_DIGEST_HOUR, minute=0, id='daily_report')

# ---------------------------
# Restart logic (in-process)
# ---------------------------
# To support token rotation, we implement a graceful stop/start of the Application.
# Note: in-process restarts can be fragile; for production prefer platform-managed restarts.
_app_lock = threading.Lock()

def register_handlers(application: Application):
    # user commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("setmode", setmode))
    application.add_handler(CommandHandler("remember", remember))
    application.add_handler(CommandHandler("recall", recall))
    application.add_handler(CommandHandler("remindme", remindme))
    application.add_handler(CommandHandler("search", search_cmd))
    application.add_handler(CommandHandler("tts", tts_cmd))
    application.add_handler(CommandHandler("checkin", checkin_cmd))
    application.add_handler(CommandHandler("credits", credits_cmd))
    application.add_handler(CommandHandler("refer", refer_cmd))
    application.add_handler(CommandHandler("claimref", claimref_cmd))
    application.add_handler(CommandHandler("leaderboard", leaderboard_cmd))
    application.add_handler(CommandHandler("contact_admin", contact_admin))
    application.add_handler(CommandHandler("feedback", feedback_cmd))
    # admin commands
    application.add_handler(CommandHandler("inbox", inbox_cmd))
    application.add_handler(CommandHandler("reply_user", reply_user_cmd))
    application.add_handler(CommandHandler("mark_handled", mark_msg_handled_cmd))
    application.add_handler(CommandHandler("feedback_inbox", feedback_inbox_cmd))
    application.add_handler(CommandHandler("reply_feedback", reply_feedback_cmd))
    application.add_handler(CommandHandler("setcredits", admin_setcredits))
    application.add_handler(CommandHandler("addcredits", admin_addcredits))
    application.add_handler(CommandHandler("ban", admin_ban))
    application.add_handler(CommandHandler("unban", admin_unban))
    application.add_handler(CommandHandler("stats", stats_cmd))
    application.add_handler(CommandHandler("setenv", admin_setenv))
    application.add_handler(CommandHandler("getenv", admin_getenv))
    application.add_handler(CommandHandler("delenv", admin_delenv))
    application.add_handler(CommandHandler("listenv", admin_listenv))
    application.add_handler(CommandHandler("add_tg_token", admin_add_tg_token))
    application.add_handler(CommandHandler("list_tg_tokens", admin_list_tg_tokens))
    application.add_handler(CommandHandler("apply_tg_token", admin_apply_tg_token))
    # message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, gemini_response))

async def restart_application_with_token(new_token: str):
    """
    Gracefully stop the current application and start a new one with new_token.
    """
    with _app_lock:
        old_app = globals().get('APPLICATION')
        if old_app:
            try:
                await old_app.stop()
                await old_app.shutdown()
            except Exception as e:
                logger.warning("Error stopping old app: %s", e)
        # build new app
        new_app = Application.builder().token(new_token).build()
        register_handlers(new_app)
        globals()['APPLICATION'] = new_app
        # start new app
        await new_app.initialize()
        await new_app.start()
        # start polling in background
        loop = asyncio.get_event_loop()
        loop.create_task(new_app.updater.start_polling())

# ---------------------------
# Admin ban helpers
# ---------------------------
def ban_user(user_id: int):
    set_memory(user_id, "banned", "1")

def unban_user(user_id: int):
    set_memory(user_id, "banned", "0")

# ---------------------------
# Main entrypoint
# ---------------------------
def main():
    global TELEGRAM_BOT_TOKEN
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set. Exiting.")
        return
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    register_handlers(application)
    globals()['APPLICATION'] = application
    # schedule daily tasks
    schedule_daily_tasks(application)
    # start polling (blocking)
    logger.info("Bot starting with token (active). Press Ctrl-C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
