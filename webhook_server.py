"""Flask сервер для приема входящих webhook'ов"""
from flask import Flask, request, jsonify
import logging
import asyncio
import threading
import concurrent.futures
from typing import Optional

logger = logging.getLogger(__name__)

class WebhookServer:
    def __init__(self, bot_instance, host='0.0.0.0', port=8080):
        self.bot = bot_instance
        self.app = Flask(__name__)
        self.host = host
        self.port = port
        self.setup_routes()
        
    def setup_routes(self):
        """Настройка маршрутов для webhook'ов"""
        
        @self.app.route('/webhook/n8n/spreadsheet', methods=['POST'])
        def handle_n8n_spreadsheet():
            """Обрабатывает входящий webhook от N8N с информацией о таблице"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No JSON data provided'}), 400
                
                logger.info(f"📨 Получен N8N webhook: {data}")
                
                # Детальное логирование полученных данных
                logger.info(f"🔍 N8N webhook детали:")
                logger.info(f"  - request_id: {data.get('request_id', 'НЕ УКАЗАН')}")
                logger.info(f"  - status: {data.get('status', 'НЕ УКАЗАН')}")
                logger.info(f"  - spreadsheet_id: {data.get('spreadsheet_id', 'НЕ УКАЗАН')}")
                logger.info(f"  - spreadsheet_url: {data.get('spreadsheet_url', 'НЕ УКАЗАН')}")
                logger.info(f"  - sheet_title: {data.get('sheet_title', 'НЕ УКАЗАН')}")
                logger.info(f"  - error_message: {data.get('error_message', 'НЕТ')}")
                
                # Запускаем обработку в asyncio
                try:
                    # Пытаемся получить текущий loop
                    loop = asyncio.get_running_loop()
                    # Используем run_coroutine_threadsafe для безопасного выполнения
                    future = asyncio.run_coroutine_threadsafe(self.bot.handle_n8n_webhook(data), loop)
                    success = future.result(timeout=10)
                except RuntimeError:
                    # Если нет активного loop, создаем новый
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    success = loop.run_until_complete(self.bot.handle_n8n_webhook(data))
                    loop.close()
                
                if success:
                    return jsonify({'status': 'success', 'message': 'N8N webhook processed'}), 200
                else:
                    return jsonify({'status': 'error', 'message': 'Failed to process N8N webhook'}), 500
                    
            except Exception as e:
                logger.error(f"❌ Ошибка обработки N8N webhook: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/webhook/system/response', methods=['POST'])
        def handle_system_response():
            """Обрабатывает ответы от систем (ready статус)"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No JSON data provided'}), 400
                
                logger.info(f"📨 Получен ответ от системы: {data}")
                
                # Запускаем обработку в asyncio
                try:
                    # Пытаемся получить текущий loop
                    loop = asyncio.get_running_loop()
                    # Используем run_coroutine_threadsafe для безопасного выполнения
                    future = asyncio.run_coroutine_threadsafe(self.bot.handle_webhook_response(data), loop)
                    success = future.result(timeout=10)
                except RuntimeError:
                    # Если нет активного loop, создаем новый
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    success = loop.run_until_complete(self.bot.handle_webhook_response(data))
                    loop.close()
                
                if success:
                    return jsonify({'status': 'success', 'message': 'System response processed'}), 200
                else:
                    return jsonify({'status': 'error', 'message': 'Failed to process system response'}), 500
                    
            except Exception as e:
                logger.error(f"❌ Ошибка обработки ответа системы: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Проверка здоровья сервера"""
            return jsonify({
                'status': 'healthy',
                'bot_running': True,
                'endpoints': [
                    '/webhook/n8n/spreadsheet',
                    '/webhook/system/response',
                    '/health'
                ]
            }), 200
        
        @self.app.route('/', methods=['GET'])
        def root():
            """Корневой маршрут"""
            return jsonify({
                'service': 'Telegram Bot Webhook Server',
                'version': '1.0',
                'endpoints': {
                    'n8n_spreadsheet': '/webhook/n8n/spreadsheet',
                    'system_response': '/webhook/system/response', 
                    'health': '/health'
                }
            }), 200
    
    def start_server(self):
        """Запускает Flask сервер в отдельном потоке"""
        def run_server():
            logger.info(f"🚀 Запуск webhook сервера на {self.host}:{self.port}")
            self.app.run(
                host=self.host,
                port=self.port,
                debug=False,
                use_reloader=False,
                threaded=True
            )
        
        # Запускаем сервер в отдельном потоке
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        logger.info(f"✅ Webhook сервер запущен в фоновом потоке")
        
        return server_thread


# Тестирование сервера
def test_webhook_server():
    """Тестирование webhook сервера"""
    import requests
    import time
    
    # Создаем мок-бота для тестирования
    class MockBot:
        async def handle_n8n_webhook(self, data):
            print(f"🧪 Тест N8N webhook: {data}")
            return True
            
        async def handle_webhook_response(self, data):
            print(f"🧪 Тест system response: {data}")
            return True
    
    # Запускаем тестовый сервер
    mock_bot = MockBot()
    server = WebhookServer(mock_bot, port=8081)
    server.start_server()
    
    time.sleep(1)  # Ждем запуска сервера
    
    print("🧪 ТЕСТИРОВАНИЕ WEBHOOK СЕРВЕРА:")
    print("=" * 50)
    
    base_url = "http://localhost:8081"
    
    # Тест health check
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✅ Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    # Тест N8N webhook
    try:
        n8n_data = {
            "request_id": "test_123",
            "status": "success",
            "spreadsheet_id": "TEST_ID",
            "spreadsheet_url": "https://test.com",
            "sheet_title": "Test Sheet"
        }
        response = requests.post(f"{base_url}/webhook/n8n/spreadsheet", json=n8n_data)
        print(f"✅ N8N webhook: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ N8N webhook failed: {e}")
    
    # Тест system response webhook
    try:
        system_data = {
            "webhook_id": "webhook_1",
            "status": "ready",
            "user_id": "12345"
        }
        response = requests.post(f"{base_url}/webhook/system/response", json=system_data)
        print(f"✅ System response: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ System response failed: {e}")


if __name__ == '__main__':
    test_webhook_server()
    input("Нажмите Enter для завершения...")
