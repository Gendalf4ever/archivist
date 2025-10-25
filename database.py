# database.py - Работа с базой данных

from datetime import datetime
from urllib.parse import urlparse
import logging
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from config import DATABASE_URL

logger = logging.getLogger(__name__)

Base = declarative_base()

class Link(Base):
    __tablename__ = 'links'
    id = Column(Integer, primary_key=True)
    chat_id = Column(String)
    user_id = Column(String)
    username = Column(String)
    url = Column(Text)
    domain = Column(String)
    title = Column(Text, nullable=True)  # ИЗМЕНЕНО: nullable=True для совместимости со старыми БД
    timestamp = Column(DateTime, default=datetime.now)
    message_text = Column(Text)

class Preset(Base):
    __tablename__ = 'presets'
    id = Column(Integer, primary_key=True)
    chat_id = Column(String)
    preset_name = Column(String)
    search_term = Column(String)
    created_at = Column(DateTime, default=datetime.now)

# Инициализация БД
engine = create_engine(DATABASE_URL)

# Пытаемся создать таблицы, если их еще нет
try:
    Base.metadata.create_all(engine)
    logger.info("Database initialized")
    
    # Миграция: добавляем колонку title если её еще нет
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    
    # Проверяем есть ли колонка title в таблице links
    if 'links' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('links')]
        if 'title' not in columns:
            logger.info("Adding title column to links table...")
            try:
                with engine.begin() as conn:
                    conn.execute(text("ALTER TABLE links ADD COLUMN title TEXT"))
                logger.info("Migration completed: title column added")
            except Exception as migrate_err:
                logger.warning(f"Could not add title column (may already exist): {migrate_err}")
    
except Exception as e:
    print(f"Ошибка при инициализации БД: {e}")
    logger.error(f"Database error: {e}")

Session = sessionmaker(bind=engine)
session = Session()

# Функции для работы с ссылками
def get_domain(url):
    """Извлекает домен из URL"""
    try:
        return urlparse(url).netloc.replace('www.', '')
    except:
        return 'unknown'

def save_link(chat_id, user_id, username, url, message_text, title=None):
    """Сохраняет ссылку в БД"""
    link = Link(
        chat_id=str(chat_id),
        user_id=str(user_id),
        username=username,
        url=url,
        domain=get_domain(url),
        title=title,
        message_text=message_text
    )
    session.add(link)
    session.commit()

def get_all_links(chat_id, limit=50):
    """Получает все ссылки для чата"""
    return session.query(Link).filter_by(chat_id=str(chat_id)).order_by(Link.timestamp.desc()).limit(limit).all()

def get_youtube_links(chat_id, limit=50):
    """Получает YouTube ссылки для чата"""
    return session.query(Link).filter(
        Link.chat_id == str(chat_id),
        (Link.domain.like('%youtube.com%') | Link.domain.like('%youtu.be%'))
    ).order_by(Link.timestamp.desc()).limit(limit).all()

def create_preset(chat_id, preset_name, search_term):
    """Создает пресет (фильтр)"""
    preset = Preset(
        chat_id=str(chat_id),
        preset_name=preset_name,
        search_term=search_term
    )
    session.add(preset)
    session.commit()

def get_presets(chat_id):
    """Получает все пресеты для чата"""
    return session.query(Preset).filter_by(chat_id=str(chat_id)).order_by(Preset.created_at.desc()).all()

def get_preset(chat_id, preset_name):
    """Получает конкретный пресет"""
    return session.query(Preset).filter_by(chat_id=str(chat_id), preset_name=preset_name).first()

def preset_exists(chat_id, preset_name):
    """Проверяет, существует ли пресет"""
    return session.query(Preset).filter_by(chat_id=str(chat_id), preset_name=preset_name).first() is not None

def search_links_by_preset(chat_id, search_term, limit=50):
    """Ищет ссылки по пресету"""
    return session.query(Link).filter(
        Link.chat_id == str(chat_id),
        (Link.url.like(f'%{search_term}%') | Link.message_text.like(f'%{search_term}%'))
    ).order_by(Link.timestamp.desc()).limit(limit).all()
