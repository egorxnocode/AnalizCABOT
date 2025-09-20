#!/bin/bash

# Скрипт остановки Telegram бота
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

echo -e "${BLUE}🛑 Остановка Telegram бота...${NC}"

# Загружаем переменные из .env
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

BOT_NAME=${BOT_NAME:-default}

# Проверяем запущен ли бот
if ! docker-compose ps | grep -q "telegram-bot-$BOT_NAME.*Up"; then
    echo -e "${YELLOW}⚠️  Бот '$BOT_NAME' не запущен${NC}"
    exit 0
fi

# Останавливаем контейнер
echo -e "${BLUE}🐳 Остановка контейнера...${NC}"
docker-compose down

# Ждем остановки
echo -e "${BLUE}⏳ Ожидание остановки...${NC}"
sleep 3

# Проверяем что контейнер остановлен
if ! docker-compose ps | grep -q "telegram-bot-$BOT_NAME.*Up"; then
    echo -e "${GREEN}✅ Бот '$BOT_NAME' успешно остановлен!${NC}"
else
    echo -e "${RED}❌ Ошибка остановки бота!${NC}"
    echo -e "${YELLOW}🔍 Принудительная остановка...${NC}"
    docker-compose kill
    echo -e "${GREEN}✅ Бот принудительно остановлен${NC}"
fi

# Показываем статус
echo -e "\n${BLUE}📊 Текущий статус:${NC}"
docker-compose ps
