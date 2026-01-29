#!/bin/bash

# Скрипт мониторинга Telegram бота
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

echo -e "${BLUE}🔍 Мониторинг бота '$BOT_NAME'${NC}"
echo -e "${BLUE}============================================${NC}"

# Функция проверки health endpoint
check_health() {
    local port=${WEBHOOK_PORT:-8080}
    local health_url="http://localhost:$port/health"
    
    echo -e "${YELLOW}Проверка health endpoint...${NC}"
    
    if curl -s -f "$health_url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Health endpoint доступен${NC}"
        return 0
    else
        echo -e "${RED}❌ Health endpoint недоступен${NC}"
        return 1
    fi
}

# Функция проверки логов на ошибки
check_logs_for_errors() {
    echo -e "${YELLOW}Проверка логов на ошибки...${NC}"
    
    if docker-compose logs --tail=50 telegram-bot 2>/dev/null | grep -i "error\|exception\|pool timeout" | tail -5; then
        echo -e "${RED}❌ Найдены ошибки в логах${NC}"
        return 1
    else
        echo -e "${GREEN}✅ Критических ошибок не найдено${NC}"
        return 0
    fi
}

# Функция проверки использования ресурсов
check_resources() {
    echo -e "${YELLOW}Проверка использования ресурсов...${NC}"
    
    if command -v docker >/dev/null 2>&1; then
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" | grep "$CONTAINER_NAME" || echo -e "${RED}❌ Контейнер не найден${NC}"
    else
        echo -e "${RED}❌ Docker не установлен${NC}"
    fi
}

# Функция автоматического перезапуска при проблемах
auto_restart_if_needed() {
    local restart_needed=false
    
    # Проверяем health endpoint
    if ! check_health; then
        restart_needed=true
    fi
    
    # Проверяем логи на критические ошибки
    if docker-compose logs --tail=20 telegram-bot 2>/dev/null | grep -q "Pool timeout\|All connections.*occupied"; then
        echo -e "${RED}❌ Обнаружены проблемы с пулом соединений${NC}"
        restart_needed=true
    fi
    
    if [ "$restart_needed" = true ]; then
        echo -e "${YELLOW}🔄 Требуется перезапуск бота...${NC}"
        ./scripts/restart.sh
        sleep 10
        check_health
    fi
}

# Основная логика мониторинга
main() {
    local mode=${1:-"check"}
    
    case $mode in
        "check")
            echo -e "${BLUE}📊 Проверка состояния...${NC}"
            ./scripts/status.sh
            echo ""
            check_health
            echo ""
            check_logs_for_errors
            echo ""
            check_resources
            ;;
        "auto-restart")
            echo -e "${BLUE}🤖 Автоматический мониторинг с перезапуском...${NC}"
            auto_restart_if_needed
            ;;
        "watch")
            echo -e "${BLUE}👁️ Непрерывный мониторинг (Ctrl+C для выхода)...${NC}"
            while true; do
                clear
                echo -e "${BLUE}🔍 Мониторинг бота '$BOT_NAME' - $(date)${NC}"
                echo -e "${BLUE}============================================${NC}"
                
                ./scripts/status.sh
                echo ""
                check_health
                echo ""
                check_logs_for_errors
                echo ""
                check_resources
                
                echo -e "\n${YELLOW}Следующая проверка через 30 секунд...${NC}"
                sleep 30
            done
            ;;
        *)
            echo "Использование: $0 [check|auto-restart|watch]"
            echo "  check        - Однократная проверка (по умолчанию)"
            echo "  auto-restart - Проверка с автоматическим перезапуском при проблемах"
            echo "  watch        - Непрерывный мониторинг"
            exit 1
            ;;
    esac
}

main "$@"