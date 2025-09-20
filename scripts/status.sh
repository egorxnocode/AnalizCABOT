#!/bin/bash

# Скрипт проверки статуса Telegram бота
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
WEBHOOK_PORT=${WEBHOOK_PORT:-8080}

echo -e "${BLUE}📊 Статус Telegram бота '$BOT_NAME'${NC}"
echo -e "${BLUE}==================================================${NC}"

# Статус контейнера
echo -e "\n${BLUE}🐳 Docker контейнер:${NC}"
if docker-compose ps | grep -q "telegram-bot-$BOT_NAME"; then
    docker-compose ps
else
    echo -e "${RED}❌ Контейнер не найден${NC}"
fi

# Проверка health check
echo -e "\n${BLUE}💚 Health Check:${NC}"
if curl -s -f "http://localhost:$WEBHOOK_PORT/health" > /dev/null 2>&1; then
    HEALTH_RESPONSE=$(curl -s "http://localhost:$WEBHOOK_PORT/health" | python3 -m json.tool 2>/dev/null || echo "Invalid JSON")
    echo -e "${GREEN}✅ Сервис доступен${NC}"
    echo "$HEALTH_RESPONSE"
else
    echo -e "${RED}❌ Сервис недоступен${NC}"
fi

# Webhook endpoints
echo -e "\n${BLUE}🌐 Webhook Endpoints:${NC}"
echo -e "  Health:       http://localhost:$WEBHOOK_PORT/health"
echo -e "  N8N:          http://localhost:$WEBHOOK_PORT/webhook/n8n/spreadsheet"
echo -e "  System resp:  http://localhost:$WEBHOOK_PORT/webhook/system/response"

# Ресурсы контейнера
echo -e "\n${BLUE}📈 Ресурсы контейнера:${NC}"
if docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -q "telegram-bot-$BOT_NAME"; then
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" "telegram-bot-$BOT_NAME" 2>/dev/null || echo "Статистика недоступна"
else
    echo -e "${RED}❌ Контейнер не запущен${NC}"
fi

# Быстрые команды
echo -e "\n${BLUE}🔧 Команды управления:${NC}"
echo -e "  Запуск:       ./scripts/start.sh"
echo -e "  Остановка:    ./scripts/stop.sh"
echo -e "  Перезапуск:   ./scripts/restart.sh"
echo -e "  Логи:         ./scripts/logs.sh"
echo -e "  Статус:       ./scripts/status.sh"
