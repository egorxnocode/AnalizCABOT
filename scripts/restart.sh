#!/bin/bash

# Скрипт перезапуска Telegram бота
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

echo -e "${BLUE}🔄 Перезапуск Telegram бота...${NC}"

# Загружаем переменные из .env
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

BOT_NAME=${BOT_NAME:-default}

echo -e "${BLUE}📊 Статус до перезапуска:${NC}"
docker-compose ps

# Останавливаем бота
echo -e "\n${YELLOW}🛑 Остановка бота...${NC}"
"$SCRIPT_DIR/stop.sh"

# Небольшая пауза
echo -e "${BLUE}⏳ Пауза перед запуском...${NC}"
sleep 2

# Запускаем бота
echo -e "\n${GREEN}🚀 Запуск бота...${NC}"
"$SCRIPT_DIR/start.sh"

echo -e "\n${GREEN}✅ Перезапуск завершен!${NC}"
