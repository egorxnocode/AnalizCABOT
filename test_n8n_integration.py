#!/usr/bin/env python3
"""
Тест интеграции с N8N для диагностики проблем с данными
"""

import requests
import json
import time
import uuid
from datetime import datetime

def test_n8n_webhook_integration():
    """Тестирование полного цикла N8N интеграции"""
    
    print("🧪 Тестирование N8N интеграции")
    print("=" * 50)
    
    # Настройки (замените на ваши)
    WEBHOOK_BASE_URL = "http://localhost:8080"  # Или IP сервера
    
    # Тест 1: Проверка health endpoint
    print("📝 Тест 1: Проверка health endpoint")
    try:
        response = requests.get(f"{WEBHOOK_BASE_URL}/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        if response.status_code == 200:
            print("✅ Health endpoint работает")
        else:
            print("❌ Health endpoint недоступен")
    except Exception as e:
        print(f"❌ Ошибка health check: {e}")
        return
    
    print("\n" + "="*50 + "\n")
    
    # Тест 2: Отправка корректного N8N webhook
    print("📝 Тест 2: Корректный N8N webhook")
    
    request_id = str(uuid.uuid4())
    correct_data = {
        "request_id": request_id,
        "status": "success",
        "spreadsheet_id": "1234567890ABCDEF",
        "spreadsheet_url": "https://docs.google.com/spreadsheets/d/1234567890ABCDEF",
        "sheet_title": "[30.01.2026] – Тестовый эксперт",
        "created_at": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(
            f"{WEBHOOK_BASE_URL}/webhook/n8n/spreadsheet",
            json=correct_data,
            timeout=10
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        if response.status_code == 200:
            print("✅ Корректный webhook обработан")
        else:
            print("❌ Ошибка обработки корректного webhook")
    except Exception as e:
        print(f"❌ Ошибка отправки корректного webhook: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Тест 3: Отправка некорректного N8N webhook (с sheetid вместо sheet_title)
    print("📝 Тест 3: Некорректный N8N webhook (с sheetid)")
    
    request_id_2 = str(uuid.uuid4())
    incorrect_data = {
        "request_id": request_id_2,
        "status": "success",
        "spreadsheet_id": "not_available",
        "spreadsheet_url": "https://docs.google.com/spreadsheets/d/not_available",
        "sheetid": "Таблица не создана",  # Неправильное поле!
        "created_at": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(
            f"{WEBHOOK_BASE_URL}/webhook/n8n/spreadsheet",
            json=incorrect_data,
            timeout=10
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        if response.status_code == 200:
            print("✅ Некорректный webhook обработан (должна быть нормализация)")
        else:
            print("❌ Ошибка обработки некорректного webhook")
    except Exception as e:
        print(f"❌ Ошибка отправки некорректного webhook: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Тест 4: Отправка webhook с пустыми данными
    print("📝 Тест 4: Webhook с пустыми данными")
    
    request_id_3 = str(uuid.uuid4())
    empty_data = {
        "request_id": request_id_3,
        "status": "success",
        "spreadsheet_id": "",  # Пусто
        "spreadsheet_url": "",  # Пусто
        "sheet_title": "",  # Пусто
    }
    
    try:
        response = requests.post(
            f"{WEBHOOK_BASE_URL}/webhook/n8n/spreadsheet",
            json=empty_data,
            timeout=10
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        if response.status_code == 200:
            print("✅ Webhook с пустыми данными обработан (должны быть значения по умолчанию)")
        else:
            print("❌ Ошибка обработки webhook с пустыми данными")
    except Exception as e:
        print(f"❌ Ошибка отправки webhook с пустыми данными: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Тест 5: Отправка webhook с ошибкой
    print("📝 Тест 5: Webhook с ошибкой N8N")
    
    request_id_4 = str(uuid.uuid4())
    error_data = {
        "request_id": request_id_4,
        "status": "error",
        "error_message": "Не удалось создать таблицу в Google Sheets",
        "spreadsheet_id": None,
        "spreadsheet_url": None,
        "sheet_title": None
    }
    
    try:
        response = requests.post(
            f"{WEBHOOK_BASE_URL}/webhook/n8n/spreadsheet",
            json=error_data,
            timeout=10
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        if response.status_code == 200:
            print("✅ Webhook с ошибкой обработан")
        else:
            print("❌ Ошибка обработки webhook с ошибкой")
    except Exception as e:
        print(f"❌ Ошибка отправки webhook с ошибкой: {e}")
    
    print("\n🎉 Тестирование завершено!")
    print("\n💡 Рекомендации:")
    print("1. Проверьте логи бота на наличие детальной информации")
    print("2. Убедитесь что N8N отправляет правильные поля")
    print("3. Проверьте что request_id совпадают между отправкой и получением")

def test_specific_issue():
    """Тест конкретной проблемы с данными"""
    print("\n" + "="*50)
    print("🔍 Тест конкретной проблемы")
    print("="*50)
    
    # Данные которые вы показали в проблеме
    problematic_data = {
        "request_id": "test-problematic-data",
        "spreadsheet_info": {
            "spreadsheet_id": "not_available",
            "spreadsheet_url": "https://docs.google.com/spreadsheets/d/not_available",
            "sheetid": "Таблица не создана",  # Проблемное поле
            "created_at": "2026-01-30T03:06:28.294023"
        }
    }
    
    print("📋 Проблемные данные:")
    print(json.dumps(problematic_data, indent=2, ensure_ascii=False))
    
    # Симулируем нормализацию
    spreadsheet_info = problematic_data["spreadsheet_info"].copy()
    
    # Исправляем sheetid -> sheet_title
    if 'sheetid' in spreadsheet_info and 'sheet_title' not in spreadsheet_info:
        spreadsheet_info['sheet_title'] = spreadsheet_info.pop('sheetid')
        print("✅ Исправлено: sheetid -> sheet_title")
    
    print("\n📋 Исправленные данные:")
    corrected_data = problematic_data.copy()
    corrected_data["spreadsheet_info"] = spreadsheet_info
    print(json.dumps(corrected_data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_n8n_webhook_integration()
    test_specific_issue()