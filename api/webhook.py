import os
import asyncio
import random
import time
from http.server import BaseHTTPRequestHandler

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, Update, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramRetryAfter, TelegramAPIError

# ==== НАСТРОЙКИ ====
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CMD_COOLDOWN = 30      # 30 секунд кд на команду
# ===================

dp = Dispatcher()

# Память
chat_cooldowns = {}    # Кд на команду
last_photo_id = {}     # ID последней картинки в чате { chat_id: message_id }

PHRASES = [
    # Ru-English (50)
    "kakashka", "top", "figna", "sueta", "kartinka", "mega top", "figna sueta", "topchik", "ne top", "real top", 
    "kruto", "zaebis", "vashpe top", "sueta sueta", "kartinka figna", "mega sueta", "lol top", "kek", "wait figna", 
    "okay top", "nice sueta", "super top", "mega kartinka", "brrr top", "figna kartinka", "top sueta", "yo top", 
    "dai kartinka", "nu figna", "nu top", "opa top", "hmm figna", "wow top", "lol figna", "sueta top", "kartinka top", 
    "top mega", "figna mega", "sueta mega", "kruto sueta", "top top", "figna figna", "kartinka kartinka", "sueta figna", 
    "vashpe figna", "real sueta", "mega lol", "top lol", "sueta lol", "kartinka lol",
    # Russian (50)
    "база", "жиза", "кринж", "топчик", "зачёт", "ну такое", "вообще база", "это кринж", "суета сует", "картинка огонь", 
    "фигня какая-то", "какашка", "вообще топ", "очень смешно", "ну фигня", "жестко", "имба", "просто имба", "такое себе", 
    "лол кек", "кекв", "орнул", "я в шоке", "нормально так", "суета", "картинка", "это база", "вот это да", "ну норм", 
    "сойдет", "жесть", "просто жесть", "огонь", "вообще огонь", "прикольно", "мило", "странно", "ну странно", "не база", 
    "кринжово", "смешно", "угар", "вообще угар", "топ база", "жиза база", "согл", "не согл", "правда", "ну правда", "капец"
]

@dp.message(Command("start"))
async def cmd_start(message: Message):
    if message.chat.type == 'private':
        await message.answer("Я жив! 🟢\nДобавь меня в группу и напиши /tgmessbotv2")

@dp.message(Command("tgmessbotv2"))
async def cmd_messbot_v2(message: Message):
    chat_id = message.chat.id
    now = time.time()

    # Проверка кд
    if now < chat_cooldowns.get(chat_id, 0):
        wait = int(chat_cooldowns[chat_id] - now)
        await message.reply(f"⏳ Подождите ещё {wait} сек. перед следующей командой!")
        return

    chat_cooldowns[chat_id] = now + CMD_COOLDOWN

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Ответ На Сообщение", callback_data="reply_pic"),
            InlineKeyboardButton(text="Сообщение", callback_data="just_msg")
        ]
    ])

    await message.answer("Привет! Я много что умею !", reply_markup=kb)

# Сохраняем ID последней картинки в чате
@dp.message(F.photo)
async def save_photo(message: Message):
    last_photo_id[message.chat.id] = message.message_id

@dp.callback_query(F.data.in_({"reply_pic", "just_msg"}))
async def handle_buttons(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    random_phrase = random.choice(PHRASES)

    if callback.data == "just_msg":
        # Просто пишет сообщение в чат
        await callback.message.answer(random_phrase)
        await callback.answer("Сообщение отправлено!")
        
    elif callback.data == "reply_pic":
        # Ищет картинку и отвечает на нее
        if chat_id in last_photo_id:
            try:
                # Пытаемся ответить на сохраненную картинку
                await callback.bot.send_message(
                    chat_id=chat_id, 
                    text=random_phrase, 
                    reply_to_message_id=last_photo_id[chat_id]
                )
                await callback.answer("Ответил на картинку!")
            except Exception as e:
                # Если картинку удалили
                await callback.message.answer(f"{random_phrase} (не смог найти картинку)")
                await callback.answer("Картинка не найдена(")
        else:
            # Если картинок вообще не было
            await callback.message.answer(f"{random_phrase} (а картинок-то и нет)")
            await callback.answer("Сначала скиньте картинку!")

# ==== ОБЕРТКА ДЛЯ VERCEL ====
async def _async_process_update(update: Update):
    bot = Bot(token=BOT_TOKEN)
    try:
        await dp.feed_update(bot, update)
    finally:
        await bot.session.close()

def _process_update(update: Update):
    try:
        asyncio.run(_async_process_update(update))
    except Exception as e:
        print("PROCESS ERROR:", repr(e))

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            update = Update.model_validate_json(body)
            _process_update(update)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
        except Exception as e:
            print("HANDLER ERROR:", repr(e))
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok": true}')

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"MessBot V2 is running")
