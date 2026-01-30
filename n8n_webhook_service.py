"""N8N Webhook сервис для двусторонней связи с созданием Google Sheets"""
import requests
import json
from datetime import datetime, timedelta
import asyncio
import logging

logger = logging.getLogger(__name__)

class N8NWebhookService:
    def __init__(self):
        # URL для отправки данных в N8N
        self.n8n_outgoing_webhook = None
        
        # Хранилище ожидающих ответов от N8N
        self.pending_requests = {}
        
    def set_outgoing_webhook(self, url):
        """Установка URL для исходящего webhook в N8N"""
        self.n8n_outgoing_webhook = url
        logger.info(f'N8N outgoing webhook установлен: {url}')
        
    async def send_data_to_n8n(self, user_id, user_data):
        """Отправка данных в N8N для создания таблицы"""
        if not self.n8n_outgoing_webhook:
            logger.error('N8N outgoing webhook не настроен')
            return False
            
        try:
            # Формирование уникального ID запроса
            request_id = f"{user_id}_{int(datetime.now().timestamp())}"
            
            # Формирование названия таблицы
            current_date = datetime.now().strftime("%d.%m.%Y")
            sheet_title = f"[{current_date}] – {user_data['profession']}"
            
            # Подготовка данных для N8N
            n8n_payload = {
                "request_id": request_id,
                "user_id": user_id,
                "action": "create_google_sheet",
                "sheet_title": sheet_title,
                "user_data": {
                    "profession": user_data['profession'],
                    "segmentation": user_data['segmentation'],
                    "ideal_client": user_data['ideal_client'],
                    "analysis_date": current_date
                },
                "spreadsheet_data": self._prepare_spreadsheet_data(user_data, current_date)
            }
            
            logger.info(f'Отправка данных в N8N для пользователя {user_id}, request_id: {request_id}')
            
            # Сохраняем запрос как ожидающий
            self.pending_requests[request_id] = {
                'user_id': user_id,
                'timestamp': datetime.now(),
                'status': 'pending'
            }
            
            # Отправляем POST запрос в N8N
            response = requests.post(
                self.n8n_outgoing_webhook,
                json=n8n_payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f'Данные успешно отправлены в N8N, request_id: {request_id}')
                return request_id
            else:
                logger.error(f'Ошибка отправки в N8N: {response.status_code} - {response.text}')
                # Удаляем из ожидающих при ошибке
                if request_id in self.pending_requests:
                    del self.pending_requests[request_id]
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f'Ошибка соединения с N8N: {e}')
            return False
        except Exception as e:
            logger.error(f'Общая ошибка отправки в N8N: {e}')
            return False
    
    def _prepare_spreadsheet_data(self, user_data, current_date):
        """Подготовка данных для таблицы"""
        return [
            ['🎯 АНАЛИЗ ЦЕЛЕВОЙ АУДИТОРИИ', ''],
            ['', ''],
            ['Параметр', 'Значение'],
            ['Профессия эксперта', user_data['profession']],
            ['Сегментация эксперта', user_data['segmentation']],
            ['Портрет идеального клиента', user_data['ideal_client']],
            ['Дата анализа', current_date],
            ['', ''],
            ['📋 РЕКОМЕНДАЦИИ ДЛЯ ДАЛЬНЕЙШЕЙ РАБОТЫ', ''],
            ['', ''],
            ['Основные характеристики ЦА', 'Заполнить на основе описания'],
            ['Боли и проблемы ЦА', 'Заполнить на основе описания'],
            ['Потребности и желания', 'Заполнить на основе исследования'],
            ['Каналы коммуникации', 'Заполнить на основе исследования'],
            ['Следующие шаги', 'Заполнить после анализа']
        ]
    
    def handle_incoming_webhook(self, webhook_data):
        """Обработка входящего webhook от N8N с информацией о созданной таблице"""
        try:
            request_id = webhook_data.get('request_id')
            if not request_id:
                logger.error('Получен webhook без request_id')
                return False
            
            if request_id not in self.pending_requests:
                logger.warning(f'Получен webhook для неизвестного request_id: {request_id}')
                return False
            
            # Извлекаем информацию о таблице
            spreadsheet_info = {
                'request_id': request_id,
                'spreadsheet_id': webhook_data.get('spreadsheet_id'),
                'spreadsheet_url': webhook_data.get('spreadsheet_url'),
                'sheet_title': webhook_data.get('sheet_title'),
                'status': webhook_data.get('status', 'success'),
                'error_message': webhook_data.get('error_message'),
                'created_at': datetime.now()
            }
            
            # Проверяем валидность критически важных данных
            missing_fields = []
            if not spreadsheet_info['spreadsheet_id']:
                missing_fields.append('spreadsheet_id')
            if not spreadsheet_info['spreadsheet_url']:
                missing_fields.append('spreadsheet_url')
            if not spreadsheet_info['sheet_title']:
                missing_fields.append('sheet_title')
            
            if missing_fields:
                logger.warning(f'⚠️ N8N webhook содержит пустые обязательные поля: {missing_fields}')
                logger.warning(f'🔍 Полученные данные: {webhook_data}')
                
                # Устанавливаем значения по умолчанию для пустых полей
                if not spreadsheet_info['spreadsheet_id']:
                    spreadsheet_info['spreadsheet_id'] = 'not_available'
                if not spreadsheet_info['spreadsheet_url']:
                    spreadsheet_info['spreadsheet_url'] = 'https://docs.google.com/spreadsheets/d/not_available'
                if not spreadsheet_info['sheet_title']:
                    spreadsheet_info['sheet_title'] = 'Таблица не создана'
            
            # Обновляем статус запроса
            self.pending_requests[request_id].update({
                'status': 'completed',
                'spreadsheet_info': spreadsheet_info,
                'completed_at': datetime.now()
            })
            
            logger.info(f'✅ Получена информация о таблице для request_id: {request_id}')
            logger.info(f'📊 Детали таблицы:')
            logger.info(f'  - Spreadsheet ID: {spreadsheet_info["spreadsheet_id"]}')
            logger.info(f'  - Spreadsheet URL: {spreadsheet_info["spreadsheet_url"]}')
            logger.info(f'  - Sheet Title: {spreadsheet_info["sheet_title"]}')
            logger.info(f'  - Status: {spreadsheet_info["status"]}')
            logger.info(f'  - Error Message: {spreadsheet_info["error_message"]}')
            logger.info(f'  - Created At: {spreadsheet_info["created_at"]}')
            
            return True
            
        except Exception as e:
            logger.error(f'Ошибка обработки входящего webhook: {e}')
            return False
    
    def get_spreadsheet_info(self, request_id):
        """Получение информации о таблице по request_id"""
        if request_id not in self.pending_requests:
            return None
            
        request_info = self.pending_requests[request_id]
        if request_info['status'] == 'completed':
            return request_info.get('spreadsheet_info')
        
        return None
    
    def is_request_completed(self, request_id):
        """Проверка завершен ли запрос"""
        if request_id not in self.pending_requests:
            return False
        return self.pending_requests[request_id]['status'] == 'completed'
    
    def cleanup_old_requests(self, hours=24):
        """Очистка старых запросов"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        to_remove = []
        for request_id, request_info in self.pending_requests.items():
            if request_info['timestamp'] < cutoff_time:
                to_remove.append(request_id)
        
        for request_id in to_remove:
            del self.pending_requests[request_id]
            logger.info(f'Удален старый запрос: {request_id}')
    
    def get_pending_requests_count(self):
        """Получение количества ожидающих запросов"""
        return len([r for r in self.pending_requests.values() if r['status'] == 'pending'])
    
    def get_completed_requests_count(self):
        """Получение количества завершенных запросов"""
        return len([r for r in self.pending_requests.values() if r['status'] == 'completed'])


def test_n8n_webhook_service():
    """Тестирование N8N webhook сервиса"""
    print('🔧 ТЕСТИРОВАНИЕ N8N WEBHOOK SERVICE:')
    print('='*50)
    
    service = N8NWebhookService()
    
    # Устанавливаем тестовый webhook URL
    test_webhook_url = input('📝 Введите N8N outgoing webhook URL (или Enter для пропуска): ').strip()
    
    if not test_webhook_url:
        print('⚠️ Webhook URL не указан, тест пропущен')
        return
    
    service.set_outgoing_webhook(test_webhook_url)
    
    # Тестовые данные
    test_data = {
        'profession': 'N8N ТЕСТ - Digital маркетолог',
        'segmentation': 'Помогаю бизнесу через N8N webhooks',
        'ideal_client': 'Владельцы интернет-магазинов с двусторонней связью'
    }
    
    # Отправка данных
    import asyncio
    
    async def test_send():
        request_id = await service.send_data_to_n8n(12345, test_data)
        if request_id:
            print(f'✅ Данные отправлены, request_id: {request_id}')
            print(f'📊 Ожидающих запросов: {service.get_pending_requests_count()}')
            
            # Симуляция получения ответа от N8N
            print('\n📋 Для завершения теста симулируйте входящий webhook:')
            print(f'{{')
            print(f'  "request_id": "{request_id}",')
            print(f'  "spreadsheet_id": "1ABC123DEF456",')
            print(f'  "spreadsheet_url": "https://docs.google.com/spreadsheets/d/1ABC123DEF456/edit",')
            print(f'  "sheet_title": "Тестовая таблица",')
            print(f'  "status": "success"')
            print(f'}}')
        else:
            print('❌ Не удалось отправить данные')
    
    asyncio.run(test_send())


if __name__ == '__main__':
    test_n8n_webhook_service()
