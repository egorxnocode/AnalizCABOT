"""Конфигурация для бота анализа ЦА"""
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram настройки
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Google API настройки
GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
GOOGLE_DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID')

# Webhook настройки
WEBHOOKS = {
    'webhook_1': os.getenv('WEBHOOK_URL_1'),
    'webhook_2': os.getenv('WEBHOOK_URL_2'),
    'webhook_3': os.getenv('WEBHOOK_URL_3'),
    'webhook_4': os.getenv('WEBHOOK_URL_4'),
    'webhook_5': os.getenv('WEBHOOK_URL_5'),
    'webhook_6': os.getenv('WEBHOOK_URL_6'),
    'webhook_7': os.getenv('WEBHOOK_URL_7'),
    'webhook_8': os.getenv('WEBHOOK_URL_8'),
    'webhook_9': os.getenv('WEBHOOK_URL_9'),
}

# N8N настройки
N8N_SHEETS_WEBHOOK_URL = os.getenv('N8N_SHEETS_WEBHOOK_URL')  # Старая переменная (deprecated)
N8N_OUTGOING_WEBHOOK_URL = os.getenv('N8N_OUTGOING_WEBHOOK_URL')  # Новая для отправки данных

# Сообщения бота
WELCOME_MESSAGE = """
👋 Привет! Я помогу вам провести анализ целевой аудитории.

Для создания детального анализа мне нужно задать вам несколько вопросов, а затем я создам для вас Google-документ с результатами.

Готовы начать?
"""

QUESTIONS = {
    'profession': 'Напишите профессию эксперта?',
    'segmentation': '''Напишите сегментацию эксперта по формуле:

Я [ВАША НИША] и помогаю [КОМУ - краткое описание вашего идеального клиента] справиться/избавиться с/от [ОПИСАНИЕ КОНКРЕТНОЙ ПРОБЛЕМЫ]. После работы со мной клиент получает [КОНКРЕТНЫЙ РЕЗУЛЬТАТ]''',
    'ideal_client': 'Опишите портрет идеального клиента'
}
