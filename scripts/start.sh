#!/bin/bash

# Скрипт запуска Telegram бота
set -e

# Определяем директорию скрипта
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Переходим в директорию проекта
cd "$PROJECT_DIR"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Запуск Telegram бота...${NC}"

# Проверяем наличие .env файла
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Файл .env не найден!${NC}"
    echo -e "${YELLOW}💡 Создайте .env файл на основе env_example${NC}"
    exit 1
fi

# Проверяем наличие credentials.json
if [ ! -f "credentials.json" ]; then
    echo -e "${RED}❌ Файл credentials.json не найден!${NC}"
    echo -e "${YELLOW}💡 Добавьте файл с учетными данными Google API${NC}"
    exit 1
fi

# Загружаем переменные из .env
export $(grep -v '^#' .env | xargs)

# Проверяем что BOT_NAME задан
if [ -z "$BOT_NAME" ]; then
    echo -e "${RED}❌ BOT_NAME не задан в .env файле!${NC}"
    exit 1
fi

# Проверяем не запущен ли уже бот
if docker-compose ps | grep -q "telegram-bot-$BOT_NAME.*Up"; then
    echo -e "${YELLOW}⚠️  Бот '$BOT_NAME' уже запущен!${NC}"
    echo -e "${BLUE}📊 Статус:${NC}"
    docker-compose ps
    exit 0
fi

# Создаем директорию для логов если её нет
mkdir -p logs

# Собираем и запускаем контейнер
echo -e "${BLUE}🔨 Сборка Docker образа...${NC}"
docker-compose build

echo -e "${BLUE}🐳 Запуск контейнера...${NC}"
docker-compose up -d

# Ждем запуска
echo -e "${BLUE}⏳ Ожидание запуска сервисов...${NC}"
sleep 5

# Проверяем статус
if docker-compose ps | grep -q "telegram-bot-$BOT_NAME.*Up"; then
    echo -e "${GREEN}✅ Бот '$BOT_NAME' успешно запущен!${NC}"
    
    # Показываем информацию о контейнере
    echo -e "\n${BLUE}📊 Информация о контейнере:${NC}"
    docker-compose ps
    
    # Показываем порты
    WEBHOOK_PORT=${WEBHOOK_PORT:-8080}
    echo -e "\n${BLUE}🌐 Webhook endpoints:${NC}"
    echo -e "  Health check: http://localhost:$WEBHOOK_PORT/health"
    echo -e "  N8N webhook:  http://localhost:$WEBHOOK_PORT/webhook/n8n/spreadsheet"
    echo -e "  System resp:  http://localhost:$WEBHOOK_PORT/webhook/system/response"
    
    echo -e "\n${BLUE}📝 Для просмотра логов:${NC} ./scripts/logs.sh"
    echo -e "${BLUE}🛑 Для остановки:${NC}      ./scripts/stop.sh"
    echo -e "${BLUE}🔄 Для перезапуска:${NC}    ./scripts/restart.sh"
    
else
    echo -e "${RED}❌ Ошибка запуска бота!${NC}"
    echo -e "${YELLOW}📝 Проверьте логи:${NC} ./scripts/logs.sh"
    exit 1
fi
