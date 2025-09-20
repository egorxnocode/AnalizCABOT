"""Сервис для отправки данных в вебхуки"""
import asyncio
import aiohttp
import ssl
import logging
from datetime import datetime
from typing import Dict, Any, List
import config

logger = logging.getLogger(__name__)

class WebhookService:
    def __init__(self):
        self.webhooks = {k: v for k, v in config.WEBHOOKS.items() if v}  # Только заполненные URL
        self.timeout = aiohttp.ClientTimeout(total=10)  # 10 секунд таймаут
        
        # SSL контекст с отключенной верификацией для обхода проблем с сертификатами
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
    
    async def send_to_all_webhooks(self, user_data: Dict[str, Any], document_info: Dict[str, Any]) -> Dict[str, bool]:
        """
        Отправляет данные во все настроенные вебхуки параллельно
        
        Args:
            user_data: Данные пользователя (профессия, сегментация, идеальный клиент)
            document_info: Информация о созданном документе (ID, URL, название)
            
        Returns:
            Dict с результатами отправки для каждого вебхука
        """
        if not self.webhooks:
            logger.warning("Нет настроенных вебхуков для отправки")
            return {}
        
        # Подготовка данных для отправки
        payload = self._prepare_payload(user_data, document_info)
        
        # Параллельная отправка во все вебхуки
        tasks = []
        for webhook_name, webhook_url in self.webhooks.items():
            task = self._send_to_webhook(webhook_name, webhook_url, payload)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обработка результатов
        webhook_results = {}
        for i, (webhook_name, _) in enumerate(self.webhooks.items()):
            result = results[i]
            if isinstance(result, Exception):
                webhook_results[webhook_name] = False
                logger.error(f"Ошибка отправки в {webhook_name}: {result}")
            else:
                webhook_results[webhook_name] = result
        
        # Логирование общих результатов
        successful = sum(1 for success in webhook_results.values() if success)
        total = len(webhook_results)
        logger.info(f"Отправлено в {successful}/{total} вебхуков")
        
        return webhook_results
    
    def _prepare_payload(self, user_data: Dict[str, Any], document_info: Dict[str, Any]) -> Dict[str, Any]:
        """Подготавливает данные для отправки в вебхук"""
        return {
            "timestamp": datetime.now().isoformat(),
            "event_type": "target_audience_analysis_completed",
            "user_data": {
                "profession": user_data.get('profession', ''),
                "segmentation": user_data.get('segmentation', ''),
                "ideal_client": user_data.get('ideal_client', ''),
            },
            "document": {
                "id": document_info.get('document_id', ''),
                "title": document_info.get('title', ''),
                "url": document_info.get('url', ''),
                "created_at": datetime.now().isoformat()
            },
            "analysis_data": {
                "profession": user_data.get('profession', ''),
                "segmentation": user_data.get('segmentation', ''),
                "ideal_client_portrait": user_data.get('ideal_client', ''),
                "analysis_date": datetime.now().strftime("%d.%m.%Y"),
                "characteristics": "Заполнить на основе описания",
                "pain_points": "Заполнить на основе описания", 
                "needs_and_desires": "Заполнить на основе описания",
                "communication_channels": "Заполнить на основе исследования",
                "recommendations": "Заполнить после анализа"
            }
        }
    
    async def _send_to_webhook(self, webhook_name: str, webhook_url: str, payload: Dict[str, Any]) -> bool:
        """
        Отправляет данные в один вебхук
        
        Args:
            webhook_name: Название вебхука для логирования
            webhook_url: URL вебхука
            payload: Данные для отправки
            
        Returns:
            True если отправка успешна, False иначе
        """
        try:
            # Создаем connector с отключенной SSL верификацией
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            async with aiohttp.ClientSession(timeout=self.timeout, connector=connector) as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    headers={
                        'Content-Type': 'application/json',
                        'User-Agent': 'TelegramBot-TargetAudience/1.0'
                    }
                ) as response:
                    if response.status in [200, 201, 202]:
                        logger.info(f"✅ Успешно отправлено в {webhook_name} (статус: {response.status})")
                        return True
                    else:
                        response_text = await response.text()
                        logger.error(f"❌ Ошибка отправки в {webhook_name}: {response.status} - {response_text}")
                        return False
                        
        except asyncio.TimeoutError:
            logger.error(f"❌ Таймаут при отправке в {webhook_name}")
            return False
        except aiohttp.ClientError as e:
            logger.error(f"❌ Ошибка клиента при отправке в {webhook_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка при отправке в {webhook_name}: {e}")
            return False
    
    def get_configured_webhooks_count(self) -> int:
        """Возвращает количество настроенных вебхуков"""
        return len(self.webhooks)
    
    def get_webhook_names(self) -> List[str]:
        """Возвращает список названий настроенных вебхуков"""
        return list(self.webhooks.keys())

# Пример использования для тестирования
async def test_webhooks():
    """Функция для тестирования вебхуков"""
    service = WebhookService()
    
    test_user_data = {
        'profession': 'Консультант по маркетингу',
        'segmentation': 'Я маркетолог и помогаю малому бизнесу увеличить продажи через digital каналы. После работы со мной клиент получает стабильный поток заявок.',
        'ideal_client': 'Собственники малого бизнеса, 30-45 лет, которые хотят масштабировать бизнес но не знают как правильно настроить маркетинг.'
    }
    
    test_document_info = {
        'document_id': 'test_doc_123',
        'title': '[18.09.2025] – Консультант по маркетингу',
        'url': 'https://docs.google.com/document/d/test_doc_123/edit'
    }
    
    results = await service.send_to_all_webhooks(test_user_data, test_document_info)
    print(f"Результаты тестирования: {results}")

if __name__ == "__main__":
    # Для тестирования
    asyncio.run(test_webhooks())

