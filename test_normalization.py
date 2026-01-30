#!/usr/bin/env python3
"""
Тест нормализации данных spreadsheet_info
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot import TargetAudienceBot
from datetime import datetime

def test_normalization():
    """Тестирование нормализации данных о таблице"""
    bot = TargetAudienceBot()
    
    print("🧪 Тестирование нормализации данных spreadsheet_info")
    print("=" * 50)
    
    # Тест 1: Данные с неправильным полем sheetid
    test_data_1 = {
        "spreadsheet_id": "not_available",
        "spreadsheet_url": "https://docs.google.com/spreadsheets/d/not_available",
        "sheetid": "Таблица не создана",  # Неправильное поле!
        "created_at": "2026-01-30T03:06:28.294023"
    }
    
    print("📝 Тест 1: Исправление поля 'sheetid' -> 'sheet_title'")
    print(f"Входные данные: {test_data_1}")
    
    normalized_1 = bot.normalize_spreadsheet_info(test_data_1)
    print(f"Нормализованные данные: {normalized_1}")
    
    assert 'sheet_title' in normalized_1
    assert 'sheetid' not in normalized_1
    assert normalized_1['sheet_title'] == "Таблица не создана"
    print("✅ Тест 1 пройден\n")
    
    # Тест 2: Корректные данные
    test_data_2 = {
        "spreadsheet_id": "1234567890",
        "spreadsheet_url": "https://docs.google.com/spreadsheets/d/1234567890",
        "sheet_title": "Корректная таблица",
        "created_at": "2026-01-30T03:06:28.294023"
    }
    
    print("📝 Тест 2: Корректные данные (без изменений)")
    print(f"Входные данные: {test_data_2}")
    
    normalized_2 = bot.normalize_spreadsheet_info(test_data_2)
    print(f"Нормализованные данные: {normalized_2}")
    
    assert normalized_2 == test_data_2
    print("✅ Тест 2 пройден\n")
    
    # Тест 3: Пустые данные
    test_data_3 = {}
    
    print("📝 Тест 3: Пустые данные (заполнение по умолчанию)")
    print(f"Входные данные: {test_data_3}")
    
    normalized_3 = bot.normalize_spreadsheet_info(test_data_3)
    print(f"Нормализованные данные: {normalized_3}")
    
    required_fields = ['spreadsheet_id', 'spreadsheet_url', 'sheet_title', 'created_at']
    for field in required_fields:
        assert field in normalized_3
        assert normalized_3[field] is not None
    print("✅ Тест 3 пройден\n")
    
    # Тест 4: Частично заполненные данные
    test_data_4 = {
        "spreadsheet_id": "real_id",
        "sheetid": "Реальная таблица"  # Неправильное поле + отсутствуют другие
    }
    
    print("📝 Тест 4: Частично заполненные данные")
    print(f"Входные данные: {test_data_4}")
    
    normalized_4 = bot.normalize_spreadsheet_info(test_data_4)
    print(f"Нормализованные данные: {normalized_4}")
    
    assert normalized_4['spreadsheet_id'] == "real_id"
    assert normalized_4['sheet_title'] == "Реальная таблица"
    assert 'sheetid' not in normalized_4
    assert 'spreadsheet_url' in normalized_4
    assert 'created_at' in normalized_4
    print("✅ Тест 4 пройден\n")
    
    print("🎉 Все тесты пройдены успешно!")

if __name__ == "__main__":
    test_normalization()