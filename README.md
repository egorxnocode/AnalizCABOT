# 🤖 Telegram Bot - Анализ Целевой Аудитории

Telegram бот для анализа целевой аудитории с интеграцией Google Sheets, N8N и внешних систем.

## 🚀 Быстрый старт

### 1. Подготовка

```bash
# Клонируйте проект
git clone <repository>
cd analiz-ca

# Создайте .env файл
cp env_example .env
# Отредактируйте .env файл с вашими настройками

# Добавьте credentials.json (Google API)
# Поместите файл в корень проекта
```

### 2. Запуск бота

```bash
# Запуск
./scripts/start.sh

# Просмотр логов в реальном времени
./scripts/logs.sh

# Проверка статуса
./scripts/status.sh

# Остановка
./scripts/stop.sh

# Перезапуск
./scripts/restart.sh
```

## 🐳 Docker конфигурация

### Особенности для нескольких ботов

Каждый бот изолирован в своем контейнере:

- **Уникальное имя**: `BOT_NAME` в .env
- **Уникальный порт**: `WEBHOOK_PORT` в .env  
- **Отдельная сеть**: `telegram-bot-network-{BOT_NAME}`
- **Отдельные логи**: в папке `logs/`

### Пример для 3 ботов

**Бот 1** (порт 8080):
```env
BOT_NAME=analiz-ca-bot
WEBHOOK_PORT=8080
TELEGRAM_BOT_TOKEN=bot1_token
```

**Бот 2** (порт 8081):
```env
BOT_NAME=support-bot  
WEBHOOK_PORT=8081
TELEGRAM_BOT_TOKEN=bot2_token
```

**Бот 3** (порт 8082):
```env
BOT_NAME=sales-bot
WEBHOOK_PORT=8082
TELEGRAM_BOT_TOKEN=bot3_token
```

## 🌐 API Endpoints

Каждый бот предоставляет webhook endpoints:

- **Health Check**: `http://localhost:{WEBHOOK_PORT}/health`
- **N8N Webhook**: `http://localhost:{WEBHOOK_PORT}/webhook/n8n/spreadsheet`
- **System Response**: `http://localhost:{WEBHOOK_PORT}/webhook/system/response`

## 📋 Рабочий процесс

1. **Пользователь заполняет форму** (профессия, сегментация, портрет клиента)
2. **Отправка в N8N** → создание Google Sheets
3. **Получение таблицы** ← webhook от N8N с информацией о таблице
4. **Последовательная отправка в системы** → 9 webhook'ов по очереди
5. **Ожидание ready** ← каждая система отвечает "ready"
6. **Финальное уведомление** → пользователю с ссылкой на таблицу

## 🔧 Управление

### Команды

| Команда | Описание |
|---------|----------|
| `./scripts/start.sh` | Запуск бота |
| `./scripts/stop.sh` | Остановка бота |
| `./scripts/restart.sh` | Перезапуск бота |
| `./scripts/logs.sh` | Логи в реальном времени |
| `./scripts/status.sh` | Статус и информация |

### Мониторинг

```bash
# Статус всех контейнеров
docker ps

# Ресурсы
docker stats

# Логи конкретного бота
docker logs telegram-bot-{BOT_NAME} -f
```

## 📝 Конфигурация

### Обязательные параметры

- `BOT_NAME` - уникальное имя бота
- `TELEGRAM_BOT_TOKEN` - токен от @BotFather
- `WEBHOOK_PORT` - уникальный порт для webhook'ов
- `credentials.json` - файл Google API

### Опциональные параметры

- `N8N_OUTGOING_WEBHOOK_URL` - URL N8N для создания таблиц
- `WEBHOOK_URL_1-9` - URL'ы внешних систем
- `GOOGLE_DRIVE_FOLDER_ID` - папка для сохранения таблиц

## 🛡️ Безопасность

- Контейнеры запускаются от непривилегированного пользователя
- Каждый бот изолирован в отдельной сети
- Логи ограничены по размеру (10MB, 3 файла)
- Health check для мониторинга состояния

## 🔍 Отладка

### Проблемы запуска

```bash
# Проверка логов
./scripts/logs.sh

# Проверка конфигурации
./scripts/status.sh

# Перезапуск с чистого листа
./scripts/stop.sh
docker-compose down --volumes
./scripts/start.sh
```

### Проверка webhook'ов

```bash
# Health check
curl http://localhost:8080/health

# Тест N8N webhook
curl -X POST http://localhost:8080/webhook/n8n/spreadsheet \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

## 📊 Структура проекта

```
analiz-ca/
├── bot.py                          # Основной файл бота
├── config.py                       # Конфигурация
├── google_minimal_service.py       # Google Sheets API
├── n8n_webhook_service.py          # N8N интеграция
├── sequential_webhook_service.py   # Последовательные webhook'и
├── webhook_server.py               # Flask сервер для webhook'ов
├── webhook_service.py              # Обычные webhook'и
├── Dockerfile                      # Docker образ
├── docker-compose.yml             # Docker Compose
├── requirements.txt                # Python зависимости
├── credentials.json                # Google API ключи (не в git)
├── .env                           # Переменные окружения (не в git)
├── scripts/                       # Скрипты управления
│   ├── start.sh
│   ├── stop.sh
│   ├── restart.sh
│   ├── logs.sh
│   └── status.sh
└── logs/                          # Логи контейнера
```