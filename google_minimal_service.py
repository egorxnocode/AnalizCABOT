"""Минимальный Google Sheets сервис только с базовыми операциями"""
import os
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import config

class GoogleMinimalService:
    def __init__(self):
        # Минимальные scopes только для Sheets
        self.scopes = [
            'https://www.googleapis.com/auth/spreadsheets'
        ]
        
        try:
            self.credentials = self._get_credentials()
            self.sheets_service = build('sheets', 'v4', credentials=self.credentials)
            print('✅ Минимальный Sheets сервис создан')
        except Exception as e:
            print(f'❌ Ошибка создания сервиса: {e}')
            self.sheets_service = None

    def _get_credentials(self):
        """Получение учетных данных для Google API"""
        if not os.path.exists(config.GOOGLE_CREDENTIALS_FILE):
            raise FileNotFoundError(f"Файл credentials не найден: {config.GOOGLE_CREDENTIALS_FILE}")
        
        credentials = Credentials.from_service_account_file(
            config.GOOGLE_CREDENTIALS_FILE,
            scopes=self.scopes
        )
        
        print(f'📧 Сервисный аккаунт: {credentials.service_account_email}')
        return credentials

    def create_spreadsheet(self, user_data):
        """Создание Google таблицы минимальным способом"""
        if not self.sheets_service:
            print('❌ Sheets сервис не инициализирован')
            return None, None
            
        try:
            # Формирование названия таблицы
            current_date = datetime.now().strftime("%d.%m.%Y")
            sheet_title = f"[{current_date}] – {user_data['profession']}"
            
            print(f'📊 Создание минимальной таблицы: {sheet_title}')
            
            # Простейшее создание таблицы
            spreadsheet_body = {
                'properties': {
                    'title': sheet_title
                }
            }
            
            print('🔄 Отправка запроса в Sheets API...')
            
            spreadsheet = self.sheets_service.spreadsheets().create(
                body=spreadsheet_body
            ).execute()
            
            spreadsheet_id = spreadsheet['spreadsheetId']
            print(f'✅ Таблица создана! ID: {spreadsheet_id}')
            
            # Заполнение данными одним запросом
            print('📝 Добавление данных...')
            self._add_data_simple(spreadsheet_id, user_data, current_date)
            
            return spreadsheet_id, sheet_title
            
        except HttpError as error:
            print(f'❌ HTTP ошибка: {error}')
            print(f'Status: {error.resp.status}')
            
            if error.resp.status == 403:
                if 'permission' in str(error).lower():
                    print('💡 Нет прав - проверьте IAM роли сервисного аккаунта')
                elif 'quota' in str(error).lower():
                    print('💡 Проблема с квотой - возможно нужен биллинг')
                else:
                    print('💡 Общая проблема доступа')
            elif error.resp.status == 401:
                print('💡 Проблема аутентификации - проверьте credentials')
            
            return None, None
        except Exception as e:
            print(f'❌ Общая ошибка: {e}')
            return None, None

    def _add_data_simple(self, spreadsheet_id, user_data, current_date):
        """Простое добавление данных в таблицу"""
        try:
            values = [
                ['🎯 АНАЛИЗ ЦЕЛЕВОЙ АУДИТОРИИ'],
                [''],
                ['Профессия эксперта:', user_data['profession']],
                ['Сегментация:', user_data['segmentation']],
                ['Идеальный клиент:', user_data['ideal_client']],
                ['Дата анализа:', current_date]
            ]
            
            body = {
                'values': values
            }
            
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='A1',
                valueInputOption='RAW',
                body=body
            ).execute()
            
            print('✅ Данные добавлены')
            
        except Exception as e:
            print(f'⚠️ Ошибка добавления данных: {e}')

    def get_spreadsheet_url(self, spreadsheet_id):
        """Получение URL таблицы"""
        return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"

    def test_minimal(self):
        """Минимальный тест"""
        if not self.sheets_service:
            return False
            
        try:
            # Создание простейшей таблицы
            test_body = {
                'properties': {
                    'title': f'МИНИМАЛЬНЫЙ ТЕСТ - {datetime.now().strftime("%H:%M:%S")}'
                }
            }
            
            print('🔄 Минимальный тест создания таблицы...')
            result = self.sheets_service.spreadsheets().create(body=test_body).execute()
            test_id = result['spreadsheetId']
            
            print(f'🎉 МИНИМАЛЬНЫЙ ТЕСТ УСПЕШЕН!')
            print(f'📊 ID: {test_id}')
            print(f'🔗 URL: {self.get_spreadsheet_url(test_id)}')
            
            return True
            
        except Exception as e:
            print(f'❌ Минимальный тест не прошел: {e}')
            return False


def main():
    """Тестирование минимального сервиса"""
    print('🔧 МИНИМАЛЬНЫЙ GOOGLE SHEETS ТЕСТ:')
    print('='*50)
    
    service = GoogleMinimalService()
    
    if not service.sheets_service:
        print('❌ Не удалось создать сервис')
        return
    
    # Минимальный тест
    if service.test_minimal():
        print()
        print('✅ Минимальный сервис работает!')
        
        # Полный тест с данными
        test_data = {
            'profession': 'МИНИМАЛЬНЫЙ ТЕСТ - Маркетолог',
            'segmentation': 'Тест минимального API',
            'ideal_client': 'Тест клиент'
        }
        
        spreadsheet_id, sheet_title = service.create_spreadsheet(test_data)
        
        if spreadsheet_id:
            sheet_url = service.get_spreadsheet_url(spreadsheet_id)
            print()
            print('🎉 ПОЛНЫЙ ТЕСТ УСПЕШЕН!')
            print(f'📊 ID: {spreadsheet_id}')
            print(f'📋 Название: {sheet_title}')
            print(f'🔗 URL: {sheet_url}')
    else:
        print()
        print('❌ Минимальный тест не прошел')
        print('💡 Проверьте IAM роли сервисного аккаунта в Google Cloud Console')


if __name__ == '__main__':
    main()

