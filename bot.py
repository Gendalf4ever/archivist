import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

from config import BOT_TOKEN, BOT_USERNAME
import database as db

# Логирование
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Утилиты
def extract_links(text):
    """Извлекает ссылки из текста"""
    return re.findall(r'https?://[^\s]+', text) if text else []

def extract_youtube_title(text):
    """Пытается извлечь название видео из текста сообщения"""
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if 'youtube.com' in line or 'youtu.be' in line:
            if i > 0 and not lines[i-1].startswith('http'):
                title = lines[i-1].strip()
                if title and len(title) > 0 and len(title) < 300:
                    return title[:200]
    
    text_without_urls = re.sub(r'https?://[^\s]+', '', text).strip()
    if text_without_urls and len(text_without_urls) < 300:
        return text_without_urls[:200]
    
    return None

def get_youtube_video_title(url):
    """Получает название видео с YouTube по URL"""
    try:
        import yt_dlp
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', None)
            if title:
                logger.info(f"[YOUTUBE_FETCH] Got title: {title[:50]}")
                return title[:200]
    except Exception as e:
        logger.debug(f"[YOUTUBE_FETCH] Error: {e}")
    return None

async def send_long_message(update, text, reply_markup=None):
    """Отправляет длинное сообщение"""
    if len(text) > 4000:
        await update.message.reply_text(text[:4000], reply_markup=reply_markup)
        for i in range(4000, len(text), 4000):
            await update.message.reply_text(text[i:i+4000])
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

async def send_long_query_message(query, text, reply_markup=None):
    """Отправляет длинное сообщение через callback query"""
    if len(text) > 4000:
        await query.message.reply_text(text[:4000], reply_markup=reply_markup)
        for i in range(4000, len(text), 4000):
            await query.message.reply_text(text[i:i+4000])
    else:
        await query.message.reply_text(text, reply_markup=reply_markup)

def format_links_response(links, title, show_title=False):
    """Форматирует ответ со ссылками"""
    response = f"{title}\n\n" if title else ""
    
    if not links:
        return response + "Нет ссылок"
    
    for i, link in enumerate(links, 1):
        try:
            date = link.timestamp.strftime('%d.%m.%Y') if link.timestamp else "N/A"
        except Exception:
            date = "N/A"
        
        if show_title and link.title:
            # YouTube с названием - жирное форматирование
            response += f"{i}. <b>{link.title}</b>\n"
            response += f"🔗 <code>{link.url}</code>\n"
            response += f"👤 {link.username or 'Unknown'} | 📅 {date}\n"
            response += "\n"  # Отступ между ссылками
        else:
            response += f"{i}. <code>{link.url}</code>\n"
            response += f"👤 {link.username or 'Unknown'} | 📅 {date}\n"
            
            message_text = link.message_text or ""
            preview = message_text[:50] + "..." if len(message_text) > 50 else message_text
            if preview:
                response += f"💬 <i>{preview}</i>\n"
            
            response += "\n"  # Отступ между ссылками
    
    return response

# ===== КОМАНДЫ БОТА =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    chat_type = update.message.chat.type
    logger.info(f"[START] Chat ID: {update.message.chat_id}, Type: {chat_type}")
    
    if chat_type in ['group', 'supergroup']:
        menu = f"""
🤖 <b>Я здесь!</b>

Команды в группе (с упоминанием бота):
/all_links@{BOT_USERNAME} - Все ссылки
/youtube@{BOT_USERNAME} - YouTube ссылки
/add_preset@{BOT_USERNAME} - Создать фильтр
/my_presets@{BOT_USERNAME} - Мои фильтры

💡 <b>Просто кидай ссылки, я их сохраню!</b>
"""
        await update.message.reply_text(menu, parse_mode='HTML')
    else:
        menu = f"""
🤖 <b>Что нужно?</b>

🔗 <b>Команды:</b>
/all_links - Все ссылки
/youtube - Только ютуб
/add_preset - Создать фильтр
/my_presets - Мои фильтры

💡 <b>Просто кидай ссылки в чат</b>
"""
        keyboard = [
            [InlineKeyboardButton("🔗 Все ссылки", callback_data="all_links")],
            [InlineKeyboardButton("🎬 YouTube", callback_data="youtube")],
            [InlineKeyboardButton("📝 Мои фильтры", callback_data="my_presets")],
            [InlineKeyboardButton("➕ Создать фильтр", callback_data="add_preset_help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(menu, parse_mode='HTML', reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_text = f"""
🤖 <b>Объясняю:</b>

🔗 <b>Основные команды:</b>
/all_links или /all_links@{BOT_USERNAME} - Все ссылки
/youtube или /youtube@{BOT_USERNAME} - Ютуб ссылки  
/add_preset или /add_preset@{BOT_USERNAME} - Создать фильтр
/my_presets или /my_presets@{BOT_USERNAME} - Мои фильтры

📝 <b>Как создать фильтр:</b>
/add_preset habr habr
Потом просто пиши /habr или /habr@{BOT_USERNAME}
"""
    await update.message.reply_text(help_text, parse_mode='HTML')

async def all_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /all_links"""
    logger.info(f"[ALL_LINKS] Chat ID: {update.message.chat_id}")
    chat_id = update.message.chat_id
    links = db.get_all_links(chat_id, limit=50)
    
    if not links:
        await update.message.reply_text("Еще нет ссылок")
        return
    
    response = "Все ссылки:\n\n"
    response += format_links_response(links, "")
    
    keyboard = [[InlineKeyboardButton("Обновить", callback_data="all_links")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await send_long_message(update, response, reply_markup)

async def youtube_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /youtube"""
    logger.info(f"[YOUTUBE] Chat ID: {update.message.chat_id}")
    chat_id = update.message.chat_id
    links = db.get_youtube_links(chat_id, limit=50)
    
    if not links:
        await update.message.reply_text("Ютуб ссылок нет")
        return
    
    response = "YouTube ссылки:\n\n"
    response += format_links_response(links, "", show_title=True)
    
    keyboard = [[InlineKeyboardButton("Обновить", callback_data="youtube")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await send_long_message(update, response, reply_markup)

async def add_preset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /add_preset"""
    logger.info(f"[ADD_PRESET] Chat ID: {update.message.chat_id}")
    
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Использование: /add_preset <команда> <слово>")
        return
    
    command_name = context.args[0].lower()
    search_term = ' '.join(context.args[1:])
    chat_id = update.message.chat_id
    
    if db.preset_exists(chat_id, command_name):
        await update.message.reply_text(f"Пресет '{command_name}' уже есть")
        return
    
    db.create_preset(chat_id, command_name, search_term)
    logger.info(f"[PRESET_CREATED] Name: {command_name}")
    await update.message.reply_text(f"Пресет '{command_name}' создан!")

async def my_presets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /my_presets"""
    logger.info(f"[MY_PRESETS] Chat ID: {update.message.chat_id}")
    chat_id = update.message.chat_id
    presets = db.get_presets(chat_id)
    
    if not presets:
        keyboard = [[InlineKeyboardButton("Создать фильтр", callback_data="add_preset_help")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Фильтров нет", reply_markup=reply_markup)
        return
    
    response = "Твои фильтры:\n\n"
    for preset in presets:
        response += f"/{preset.preset_name} - {preset.search_term}\n"
    
    keyboard = [[InlineKeyboardButton("Создать еще", callback_data="add_preset_help")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(response, reply_markup=reply_markup)

async def handle_preset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик пользовательских команд"""
    text = update.message.text
    
    if not text or not text.startswith('/'):
        return
    
    command = text[1:].split('@')[0].split(' ')[0]
    chat_id = update.message.chat_id
    
    preset = db.get_preset(chat_id, command)
    if not preset:
        return
    
    logger.info(f"[HANDLE_PRESET] Command: {command}")
    links = db.search_links_by_preset(chat_id, preset.search_term, limit=50)
    
    if not links:
        await update.message.reply_text(f"По '{preset.search_term}' нет ссылок")
        return
    
    response = f"Результаты по '{preset.search_term}':\n\n"
    response += format_links_response(links, "")
    await send_long_message(update, response)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик сообщений"""
    if update.message.text and update.message.text.startswith('/'):
        return
    
    text = update.message.text or update.message.caption or ""
    if not text:
        return
    
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    
    links = extract_links(text)
    logger.debug(f"[HANDLE_MESSAGE] Found {len(links)} links")
    
    for link in links:
        title = None
        
        if 'youtube.com' in link or 'youtu.be' in link:
            title = extract_youtube_title(text)
            if not title:
                logger.debug(f"[YOUTUBE_FETCH] Fetching: {link[:50]}")
                title = get_youtube_video_title(link)
        
        db.save_link(chat_id, user_id, username, link, text, title=title)
        logger.info(f"[SAVED_LINK] URL: {link[:50]}, Title: {title[:30] if title else 'None'}")

async def new_chat_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик новых членов"""
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            await update.message.reply_text("Привет! Я здесь для сохранения ссылок")

async def handle_inline_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик inline кнопок"""
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    callback_data = query.data
    
    logger.info(f"[INLINE] Button: {callback_data}, Chat: {chat_id}, User: {query.from_user.id}")
    
    # Кнопки работают для всех пользователей в чате
    
    if callback_data == "all_links":
        links = db.get_all_links(chat_id)
        if not links:
            await query.message.reply_text("Нет ссылок")
            return
        response = "Все ссылки:\n\n" + format_links_response(links, "")
        keyboard = [[InlineKeyboardButton("Обновить", callback_data="all_links")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await send_long_query_message(query, response, reply_markup)
    
    elif callback_data == "youtube":
        links = db.get_youtube_links(chat_id)
        if not links:
            await query.message.reply_text("Нет YouTube ссылок")
            return
        response = "YouTube ссылки:\n\n" + format_links_response(links, "", show_title=True)
        keyboard = [[InlineKeyboardButton("Обновить", callback_data="youtube")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await send_long_query_message(query, response, reply_markup)
    
    elif callback_data == "my_presets":
        presets = db.get_presets(chat_id)
        if not presets:
            await query.message.reply_text("Нет фильтров")
            return
        response = "Твои фильтры:\n\n"
        for preset in presets:
            response += f"/{preset.preset_name}\n"
        keyboard = [[InlineKeyboardButton("Создать", callback_data="add_preset_help")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(response, reply_markup=reply_markup)
    
    elif callback_data == "add_preset_help":
        msg = "Создание фильтра:\n/add_preset название слово"
        keyboard = [[InlineKeyboardButton("Назад", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(msg, reply_markup=reply_markup)
    
    elif callback_data == "start":
        menu = "Меню"
        keyboard = [
            [InlineKeyboardButton("Все ссылки", callback_data="all_links")],
            [InlineKeyboardButton("YouTube", callback_data="youtube")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(menu, reply_markup=reply_markup)

def main():
    """Запуск бота"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    handlers = [
        CommandHandler("start", start),
        CommandHandler("help", help_command),
        CommandHandler("all_links", all_links),
        CommandHandler("youtube", youtube_links),
        CommandHandler("add_preset", add_preset),
        CommandHandler("my_presets", my_presets),
        CallbackQueryHandler(handle_inline_button),
        MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_chat_members),
        MessageHandler(filters.COMMAND, handle_preset),
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message),
        MessageHandler(filters.ALL & ~filters.COMMAND, handle_message)
    ]
    
    for handler in handlers:
        application.add_handler(handler)
    
    print(f"Bot started: @{BOT_USERNAME}")
    logger.info(f"Bot started with token: {BOT_TOKEN[:20]}...")
    application.run_polling()

if __name__ == '__main__':
    main()
