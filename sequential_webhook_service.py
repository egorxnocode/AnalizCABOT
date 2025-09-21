"""Сервис для последовательной отправки webhook'ов с ожиданием ответов"""
import asyncio
import aiohttp
import ssl
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import config

logger = logging.getLogger(__name__)

class SequentialWebhookService:
    def __init__(self):
        self.webhooks = {k: v for k, v in config.WEBHOOKS.items() if v}  # Только заполненные URL
        self.timeout = aiohttp.ClientTimeout(total=30)  # 30 секунд таймаут для ожидания ответа
        
        # SSL контекст с отключенной верификацией
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
        # Хранилище ожидающих ответов от webhook'ов
        self.pending_webhooks = {}  # {user_id: {webhook_responses: {}, total_count: int, completed_count: int}}
        
    async def send_webhooks_sequentially(self, user_id: int, user_data: Dict[str, Any], 
                                       spreadsheet_info: Dict[str, Any], 
                                       progress_callback) -> Dict[str, bool]:
        """
        Отправляет webhook'и последовательно с ожиданием ответа от каждого
        
        Args:
            user_id: ID пользователя
            user_data: Данные пользователя
            spreadsheet_info: Информация о таблице от N8N
            progress_callback: Функция для уведомления пользователя о прогрессе
            
        Returns:
            Dict с результатами отправки
        """
        if not self.webhooks:
            logger.warning("Нет настроенных вебхуков для отправки")
            return {}
        
        # Инициализируем состояние для пользователя
        self.pending_webhooks[user_id] = {
            'webhook_responses': {},
            'total_count': len(self.webhooks),
            'completed_count': 0,
            'spreadsheet_info': spreadsheet_info
        }
        
        results = {}
        webhook_list = list(self.webhooks.items())
        
        await progress_callback(f"🚀 Начинаю отправку в {len(webhook_list)} систем...")
        
        for i, (webhook_name, webhook_url) in enumerate(webhook_list, 1):
            await progress_callback(f"📤 Отправляю в систему {i}/{len(webhook_list)} ({webhook_name})...\n⏰ Жду ответа до 3 минут")
            
            # Подготавливаем данные с информацией о таблице
            payload = self._prepare_payload_with_spreadsheet(user_data, spreadsheet_info, webhook_name, user_id)
            
            # Отправляем webhook
            success = await self._send_webhook_and_wait(webhook_name, webhook_url, payload, user_id)
            results[webhook_name] = success
            
            if success:
                await progress_callback(f"✅ Система {i}/{len(webhook_list)} обработана успешно")
            else:
                await progress_callback(f"❌ Система {i}/{len(webhook_list)} не ответила за 3 минуты")
                await progress_callback(f"🔄 ОТЛАДКА: Продолжаю отправку в остальные системы для тестирования")
                
                # ВРЕМЕННО: НЕ прекращаем цикл при неудаче - продолжаем для отладки
                # break  # Закомментировано для отладки
                
            # Небольшая пауза между отправками
            await asyncio.sleep(0.5)
        
        # Очищаем состояние пользователя
        if user_id in self.pending_webhooks:
            del self.pending_webhooks[user_id]
            
        successful = sum(1 for success in results.values() if success)
        logger.info(f"Последовательная отправка завершена: {successful}/{len(results)} вебхуков")
        
        return results
    
    def _prepare_payload_with_spreadsheet(self, user_data: Dict[str, Any], 
                                        spreadsheet_info: Dict[str, Any],
                                        webhook_name: str, user_id: int) -> Dict[str, Any]:
        """Подготавливает данные для отправки с информацией о таблице"""
        
        # Функция для безопасного преобразования значений в JSON-сериализуемые
        def safe_json_value(value):
            if hasattr(value, 'isoformat'):  # datetime объект
                return value.isoformat()
            elif not isinstance(value, (str, int, float, bool, type(None))):
                return str(value)
            return value
        
        # Безопасно получаем и преобразуем все значения
        spreadsheet_id = safe_json_value(spreadsheet_info.get('spreadsheet_id', ''))
        spreadsheet_url = safe_json_value(spreadsheet_info.get('spreadsheet_url', ''))
        sheet_title = safe_json_value(spreadsheet_info.get('sheet_title', ''))
        created_at = safe_json_value(spreadsheet_info.get('created_at', ''))
        
        return {
            "event_type": "target_audience_analysis",
            "timestamp": datetime.now().isoformat(),
            "user_id": str(user_id),
            "webhook_name": webhook_name,
            "telegram_user_id": user_id,  # Дублируем для возврата
            "user_data": {
                "profession": user_data.get('profession', ''),
                "segmentation": user_data.get('segmentation', ''),
                "ideal_client_portrait": user_data.get('ideal_client', '')
            },
            "spreadsheet_info": {
                "spreadsheet_id": spreadsheet_id,
                "spreadsheet_url": spreadsheet_url,
                "sheetid": sheet_title,
                "created_at": created_at
            },
            "analysis_data": {
                "analysis_date": datetime.now().strftime("%d.%m.%Y"),
                "characteristics": "Заполнить на основе описания",
                "pain_points": "Заполнить на основе описания", 
                "needs_and_desires": "Заполнить на основе описания",
                "communication_channels": "Заполнить на основе исследования",
                "recommendations": "Заполнить после анализа"
            }
        }
    
    async def _send_webhook_and_wait(self, webhook_name: str, webhook_url: str, 
                                   payload: Dict[str, Any], user_id: int) -> bool:
        """
        Отправляет webhook и ждет ответа 'ready'
        
        Returns:
            True если получен ответ 'ready', False иначе
        """
        try:
            # Логируем payload для отладки (только основную информацию)
            logger.info(f"📤 ОТЛАДКА: Отправка webhook {webhook_name} в {webhook_url}")
            logger.info(f"📋 Данные: user_id={payload.get('user_id')}, event_type={payload.get('event_type')}")
            
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            async with aiohttp.ClientSession(timeout=self.timeout, connector=connector) as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    headers={
                        'Content-Type': 'application/json',
                        'User-Agent': 'TelegramBot-SequentialWebhook/1.0'
                    }
                ) as response:
                    if response.status in [200, 201, 202]:
                        logger.info(f"✅ Webhook {webhook_name} отправлен (статус: {response.status})")
                        
                        # Ждем ответа от webhook'а в течение таймаута
                        result = await self._wait_for_webhook_response(webhook_name, user_id)
                        logger.info(f"📥 ОТЛАДКА: Ответ от {webhook_name}: {'ready' if result else 'таймаут'}")
                        return result
                    else:
                        response_text = await response.text()
                        logger.error(f"❌ Ошибка отправки {webhook_name}: {response.status} - {response_text}")
                        return False
                        
        except asyncio.TimeoutError:
            logger.error(f"❌ Таймаут при отправке {webhook_name}")
            return False
        except aiohttp.ClientError as e:
            logger.error(f"❌ Ошибка клиента {webhook_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка {webhook_name}: {e}")
            return False
    
    async def _wait_for_webhook_response(self, webhook_name: str, user_id: int, 
                                       timeout_seconds: int = 180) -> bool:
        """
        Ждет ответа от webhook'а в течение 3 минут (180 секунд)
        
        Returns:
            True если получен ответ 'ready', False при таймауте
        """
        start_time = asyncio.get_event_loop().time()
        
        while True:
            # Проверяем получен ли ответ
            if (user_id in self.pending_webhooks and 
                webhook_name in self.pending_webhooks[user_id]['webhook_responses']):
                response = self.pending_webhooks[user_id]['webhook_responses'][webhook_name]
                if response.get('status') == 'ready':
                    logger.info(f"✅ Получен ответ 'ready' от {webhook_name}")
                    return True
                else:
                    logger.warning(f"⚠️ Получен неожиданный ответ от {webhook_name}: {response}")
                    return False
            
            # Проверяем таймаут
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout_seconds:
                logger.error(f"❌ Таймаут ожидания ответа от {webhook_name}")
                return False
            
            # Небольшая пауза перед следующей проверкой
            await asyncio.sleep(0.1)
    
    def handle_webhook_response(self, response_data: Dict[str, Any]) -> bool:
        """
        Обрабатывает входящий ответ от webhook'а
        
        Ожидаемый формат:
        {
            "webhook_id": "webhook_1",
            "status": "ready", 
            "user_id": "8098626207",
            "processed_at": "2024-09-20T17:16:45Z",
            "message": "Данные успешно обработаны"
        }
        """
        try:
            webhook_id = response_data.get('webhook_id')
            user_id = int(response_data.get('user_id', 0))
            status = response_data.get('status')
            
            if not webhook_id or not user_id or not status:
                logger.error(f"Неполные данные в ответе webhook: {response_data}")
                return False
            
            if user_id not in self.pending_webhooks:
                logger.warning(f"Получен ответ для неизвестного пользователя {user_id}")
                return False
            
            # Сохраняем ответ
            self.pending_webhooks[user_id]['webhook_responses'][webhook_id] = response_data
            
            logger.info(f"📨 Получен ответ от {webhook_id} для пользователя {user_id}: {status}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обработки ответа webhook: {e}")
            return False
    
    def get_configured_webhooks_count(self) -> int:
        """Возвращает количество настроенных вебхуков"""
        return len(self.webhooks)
    
    def get_webhook_names(self) -> List[str]:
        """Возвращает список названий настроенных вебхуков"""
        return list(self.webhooks.keys())


# Пример использования
async def test_sequential_webhooks():
    """Функция для тестирования последовательных webhook'ов"""
    service = SequentialWebhookService()
    
    # Тестовые данные пользователя
    user_data = {
        'profession': 'Тест последовательных webhook\'ов',
        'segmentation': 'Проверка очередности отправки',
        'ideal_client': 'Системы которые отвечают ready'
    }
    
    # Тестовая информация о таблице от N8N
    spreadsheet_info = {
        'spreadsheet_id': 'TEST123456789',
        'spreadsheet_url': 'https://docs.google.com/spreadsheets/d/TEST123456789/edit',
        'sheet_title': '[20.09.2024] – Тестовая таблица',
        'created_at': datetime.now().isoformat()
    }
    
    async def progress_callback(message):
        print(f"📊 {message}")
    
    print("🧪 ТЕСТИРОВАНИЕ ПОСЛЕДОВАТЕЛЬНЫХ WEBHOOK'ОВ:")
    print("=" * 50)
    
    results = await service.send_webhooks_sequentially(
        user_id=12345,
        user_data=user_data,
        spreadsheet_info=spreadsheet_info,
        progress_callback=progress_callback
    )
    
    print(f"\n📈 Результаты: {results}")
    
if __name__ == '__main__':
    asyncio.run(test_sequential_webhooks())
