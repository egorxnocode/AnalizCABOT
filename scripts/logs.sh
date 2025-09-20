#!/bin/bash

# Скрипт просмотра логов Telegram бота в реальном времени
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

# Загружаем переменные из .env
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

BOT_NAME=${BOT_NAME:-default}
CONTAINER_NAME="telegram-bot-$BOT_NAME"

# Проверяем запущен ли бот
if ! docker-compose ps | grep -q "$CONTAINER_NAME.*Up"; then
    echo -e "${RED}❌ Бот '$BOT_NAME' не запущен!${NC}"
    echo -e "${YELLOW}💡 Запустите бота: ./scripts/start.sh${NC}"
    exit 1
fi

echo -e "${BLUE}📝 Просмотр логов бота '$BOT_NAME' в реальном времени...${NC}"
echo -e "${YELLOW}💡 Для выхода нажмите Ctrl+C${NC}"
echo -e "${BLUE}============================================================${NC}"

# Параметры для отображения логов
LINES=${1:-100}  # Количество строк истории (по умолчанию 100)

# Показываем логи в реальном времени
docker-compose logs -f --tail="$LINES" telegram-bot
