"""Telegram бот для анализа целевой аудитории"""
import logging
from datetime import datetime
from typing import Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from google_minimal_service import GoogleMinimalService
from webhook_service import WebhookService
from n8n_webhook_service import N8NWebhookService
from sequential_webhook_service import SequentialWebhookService
from webhook_server import WebhookServer
import config

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния диалога
WAITING_FOR_PROFESSION = 1
WAITING_FOR_SEGMENTATION = 2
WAITING_FOR_IDEAL_CLIENT = 3

class TargetAudienceBot:
    def __init__(self):
        self.google_service = GoogleMinimalService()
        self.webhook_service = WebhookService()
        self.n8n_service = N8NWebhookService()
        self.sequential_webhook_service = SequentialWebhookService()
        self.application = None  # Будет установлено позже в main()
        
        # Настройка N8N webhook если URL есть в конфигурации
        if hasattr(config, 'N8N_OUTGOING_WEBHOOK_URL') and config.N8N_OUTGOING_WEBHOOK_URL:
            self.n8n_service.set_outgoing_webhook(config.N8N_OUTGOING_WEBHOOK_URL)
        
        self.user_sessions = {}  # Хранение данных пользователей
        
        # Запускаем webhook сервер
        self.webhook_server = WebhookServer(self, host='0.0.0.0', port=config.WEBHOOK_PORT)
        self.webhook_server.start_server()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user_id = update.effective_user.id
        
        # Сброс сессии пользователя
        self.user_sessions[user_id] = {}
        
        # Создание кнопки "Начать анализ ЦА"
        keyboard = [[InlineKeyboardButton("🎯 Начать анализ ЦА", callback_data='start_analysis')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            config.WELCOME_MESSAGE,
            reply_markup=reply_markup
        )

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        if query.data == 'start_analysis':
            # Начало анализа - запрос профессии
            self.user_sessions[user_id] = {'state': WAITING_FOR_PROFESSION}
            
            await query.edit_message_text(
                f"📝 {config.QUESTIONS['profession']}"
            )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        user_id = update.effective_user.id
        user_text = update.message.text
        
        # Проверяем, есть ли активная сессия
        if user_id not in self.user_sessions:
            await update.message.reply_text(
                "Пожалуйста, начните с команды /start"
            )
            return
        
        session = self.user_sessions[user_id]
        state = session.get('state')
        
        if state == WAITING_FOR_PROFESSION:
            # Сохраняем профессию и переходим к следующему вопросу
            session['profession'] = user_text
            session['state'] = WAITING_FOR_SEGMENTATION
            
            await update.message.reply_text(
                f"✅ Профессия сохранена: {user_text}\n\n"
                f"📝 {config.QUESTIONS['segmentation']}"
            )
            
        elif state == WAITING_FOR_SEGMENTATION:
            # Сохраняем сегментацию и переходим к следующему вопросу
            session['segmentation'] = user_text
            session['state'] = WAITING_FOR_IDEAL_CLIENT
            
            await update.message.reply_text(
                f"✅ Сегментация сохранена!\n\n"
                f"📝 {config.QUESTIONS['ideal_client']}"
            )
            
        elif state == WAITING_FOR_IDEAL_CLIENT:
            # Сохраняем описание клиента и создаем документ
            session['ideal_client'] = user_text
            
            await update.message.reply_text(
                "✅ Портрет идеального клиента сохранен!\n\n"
                "📊 Создаю Google-таблицу с анализом ЦА... Пожалуйста, подождите."
            )
            
            # Отправка данных в N8N для создания таблицы
            await update.message.reply_text("📤 Отправляю данные в N8N для создания таблицы...")
            
            try:
                # Отправляем данные в N8N
                request_id = await self.n8n_service.send_data_to_n8n(user_id, {
                    'profession': session['profession'],
                    'segmentation': session['segmentation'],
                    'ideal_client': session['ideal_client']
                })
                
                # Новая логика: сначала ждем ответа от N8N, потом отправляем webhook'и последовательно
                # Пока только отправляем в N8N и ждем ответа
                webhook_status = ""
                
                if request_id:
                    # Сохраняем request_id и данные пользователя в сессии
                    session['n8n_request_id'] = request_id
                    session['user_data'] = {
                        'profession': session['profession'],
                        'segmentation': session['segmentation'],
                        'ideal_client': session['ideal_client']
                    }
                    
                    await update.message.reply_text(
                        f"📊 Процесс запущен:\n"
                        f"✅ Данные отправлены в N8N\n"
                        f"📝 ID запроса: {request_id}\n\n"
                        f"⏳ Ожидаю создания таблицы в N8N...\n"
                        f"📋 После создания таблицы начну последовательную отправку в 9 систем"
                    )
                    
                    # НЕ очищаем сессию - ждем ответа от N8N
                else:
                    # N8N не сработал, но webhook'и отправлены
                    await update.message.reply_text(
                        f"📊 Статус обработки:\n"
                        f"❌ N8N: Ошибка создания таблицы\n"
                        f"{webhook_status}\n"
                        f"💡 Данные сохранены в других системах"
                    )
                    
            except Exception as e:
                logger.error(f"Ошибка при создании таблицы через API Key: {e}")
                await update.message.reply_text(
                    f"❌ Ошибка API Key сервиса: {str(e)}\n\n"
                    "💡 Возможные причины:\n"
                    "• API Key не настроен\n"
                    "• API Key недействителен\n"
                    "• Google Sheets API недоступен\n\n"
                    "Требуется настройка Google API Key."
                )
            
            # Очищаем сессию пользователя только если это НЕ N8N запрос
            if 'n8n_request_id' not in session:
                del self.user_sessions[user_id]
        
        else:
            await update.message.reply_text(
                "Я не понимаю. Пожалуйста, используйте команду /start для начала."
            )
    
    def _format_text_analysis(self, session):
        """Форматирование анализа ЦА в текстовом виде"""
        current_date = datetime.now().strftime("%d.%m.%Y")
        
        return f"""🎯 **АНАЛИЗ ЦЕЛЕВОЙ АУДИТОРИИ**
📅 Дата: {current_date}

**Профессия эксперта:**
{session['profession']}

**Сегментация эксперта:**
{session['segmentation']}

**Портрет идеального клиента:**
{session['ideal_client']}

---

📋 **РЕКОМЕНДАЦИИ ДЛЯ ДАЛЬНЕЙШЕЙ РАБОТЫ:**

• Определите основные характеристики ЦА на основе описания
• Выявите боли и проблемы целевой аудитории  
• Сформулируйте потребности и желания клиентов
• Исследуйте каналы коммуникации с ЦА
• Разработайте план следующих шагов

✅ Анализ готов для дальнейшего использования!"""

    async def handle_n8n_webhook(self, webhook_data):
        """Обработка входящего webhook от N8N с информацией о созданной таблице"""
        try:
            # Передаем данные в N8N сервис
            success = self.n8n_service.handle_incoming_webhook(webhook_data)
            
            if not success:
                logger.error('Ошибка обработки webhook от N8N')
                return False
            
            request_id = webhook_data.get('request_id')
            if not request_id:
                logger.error('Webhook без request_id')
                return False
            
            # Находим пользователя по request_id
            user_id = None
            for uid, session in self.user_sessions.items():
                if session.get('n8n_request_id') == request_id:
                    user_id = uid
                    break
            
            if not user_id:
                logger.warning(f'Пользователь не найден для request_id: {request_id}')
                return False
            
            # Получаем информацию о таблице
            spreadsheet_info = self.n8n_service.get_spreadsheet_info(request_id)
            
            if not spreadsheet_info:
                logger.error(f'Информация о таблице не найдена для request_id: {request_id}')
                return False
            
            # Уведомляем пользователя о готовой таблице и запускаем последовательные webhook'и  
            await self._start_sequential_webhooks(user_id, spreadsheet_info)
            
            return True
            
        except Exception as e:
            logger.error(f'Ошибка обработки N8N webhook: {e}')
            return False
    
    async def _notify_user_about_spreadsheet(self, user_id, spreadsheet_info):
        """Уведомление пользователя о готовой таблице"""
        try:
            # Проверяем что application инициализировано
            if not self.application:
                logger.error(f'Application не инициализировано для пользователя {user_id}')
                return
                
            if spreadsheet_info['status'] == 'success':
                # Успешное создание таблицы
                spreadsheet_id = spreadsheet_info['spreadsheet_id']
                spreadsheet_url = spreadsheet_info['spreadsheet_url']
                sheet_title = spreadsheet_info['sheet_title']
                
                # Создание кнопки для перехода к таблице
                keyboard = [[InlineKeyboardButton("📊 Открыть таблицу", url=spreadsheet_url)]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await self.application.bot.send_message(
                    chat_id=user_id,
                    text=f"🎉 Таблица готова!\n\n"
                         f"📋 Название: {sheet_title}\n"
                         f"🔗 Ссылка: {spreadsheet_url}\n"
                         f"📊 ID: {spreadsheet_id}\n\n"
                         f"Таблица содержит анализ вашей целевой аудитории.",
                    reply_markup=reply_markup
                )
                
                # Предложение начать новый анализ
                keyboard_new = [[InlineKeyboardButton("🎯 Начать новый анализ", callback_data='start_analysis')]]
                reply_markup_new = InlineKeyboardMarkup(keyboard_new)
                
                await self.application.bot.send_message(
                    chat_id=user_id,
                    text="Хотите провести еще один анализ?",
                    reply_markup=reply_markup_new
                )
                
            else:
                # Ошибка создания таблицы
                error_message = spreadsheet_info.get('error_message', 'Неизвестная ошибка')
                
                await self.application.bot.send_message(
                    chat_id=user_id,
                    text=f"❌ Ошибка создания таблицы в N8N:\n{error_message}\n\n"
                         f"Попробуйте создать анализ заново."
                )
                
        except Exception as e:
            logger.error(f'Ошибка уведомления пользователя {user_id}: {e}')

    async def _start_sequential_webhooks(self, user_id: int, spreadsheet_info: Dict[str, Any]):
        """Запускает последовательную отправку webhook'ов после получения таблицы от N8N"""
        try:
            # Проверяем что application инициализировано
            if not self.application:
                logger.error(f'Application не инициализировано для пользователя {user_id}')
                return
                
            # Получаем данные пользователя из сессии
            if user_id not in self.user_sessions:
                logger.error(f'Сессия пользователя {user_id} не найдена')
                return
                
            session = self.user_sessions[user_id]
            user_data = session.get('user_data', {})
            
            # Уведомляем о готовой таблице
            spreadsheet_url = spreadsheet_info['spreadsheet_url']
            sheet_title = spreadsheet_info['sheet_title']
            
            keyboard = [[InlineKeyboardButton("📊 Открыть таблицу", url=spreadsheet_url)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.application.bot.send_message(
                chat_id=user_id,
                text=f"🎉 Таблица создана!\n\n"
                     f"📋 Название: {sheet_title}\n"
                     f"🔗 Ссылка: {spreadsheet_url}\n\n"
                     f"🚀 Теперь начинаю последовательную отправку в 9 систем...",
                reply_markup=reply_markup
            )
            
            # Функция для уведомлений о прогрессе
            async def progress_callback(message: str):
                await self.application.bot.send_message(
                    chat_id=user_id,
                    text=message
                )
            
            # Запускаем последовательную отправку webhook'ов
            webhook_results = await self.sequential_webhook_service.send_webhooks_sequentially(
                user_id=user_id,
                user_data=user_data,
                spreadsheet_info=spreadsheet_info,
                progress_callback=progress_callback
            )
            
            # Подводим итоги
            successful = sum(1 for success in webhook_results.values() if success)
            total = len(webhook_results)
            
            await self.application.bot.send_message(
                chat_id=user_id,
                text=f"🏁 Процесс завершен!\n\n"
                     f"📊 Таблица: {sheet_title}\n"
                     f"🔗 Ссылка: {spreadsheet_url}\n"
                     f"📡 Обработано систем: {successful}/{total}\n\n"
                     f"✅ Анализ целевой аудитории готов!"
            )
            
            # Предложение начать новый анализ
            keyboard_new = [[InlineKeyboardButton("🎯 Начать новый анализ", callback_data='start_analysis')]]
            reply_markup_new = InlineKeyboardMarkup(keyboard_new)
            
            await self.application.bot.send_message(
                chat_id=user_id,
                text="Хотите провести еще один анализ?",
                reply_markup=reply_markup_new
            )
            
            # Очищаем сессию пользователя
            if user_id in self.user_sessions:
                del self.user_sessions[user_id]
                
        except Exception as e:
            logger.error(f'Ошибка запуска последовательных webhook\'ов для пользователя {user_id}: {e}')
            await self.application.bot.send_message(
                chat_id=user_id,
                text=f"❌ Ошибка при обработке систем: {str(e)}\n\n"
                     f"Таблица создана, но некоторые системы могли не получить данные."
            )

    async def handle_webhook_response(self, response_data: Dict[str, Any]):
        """Обрабатывает ответы от webhook'ов (ready статус)"""
        try:
            return self.sequential_webhook_service.handle_webhook_response(response_data)
        except Exception as e:
            logger.error(f'Ошибка обработки ответа webhook: {e}')
            return False

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок"""
        logger.error(f"Update {update} caused error {context.error}")

def main():
    """Запуск бота"""
    if not config.TELEGRAM_BOT_TOKEN:
        print("❌ Ошибка: TELEGRAM_BOT_TOKEN не установлен!")
        print("Пожалуйста, создайте файл .env и добавьте токен бота.")
        return
    
    # Создание экземпляра бота
    bot = TargetAudienceBot()
    
    # Создание приложения
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    
    # Устанавливаем application в бота для доступа к bot API
    bot.application = application
    
    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CallbackQueryHandler(bot.button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    application.add_error_handler(bot.error_handler)
    
    # Запуск бота
    print("🤖 Бот запущен! Нажмите Ctrl+C для остановки.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
