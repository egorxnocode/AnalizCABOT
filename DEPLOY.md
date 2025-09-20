# 🚀 Развертывание Telegram Bot на сервере

Подробная инструкция по развертыванию Telegram бота для анализа целевой аудитории на продакшн сервере.

## 📋 Требования к серверу

### Минимальные требования
- **OS**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **RAM**: 2GB (рекомендуется 4GB для нескольких ботов)
- **CPU**: 1 vCPU (рекомендуется 2 vCPU)
- **Диск**: 10GB свободного места
- **Порты**: 8080-8089 (для webhook'ов ботов)

### Для нескольких ботов
- **RAM**: +512MB на каждого дополнительного бота
- **Порты**: уникальный порт для каждого бота

## 🔧 Установка зависимостей

### 1. Обновление системы

```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo yum update -y
# или для новых версий
sudo dnf update -y
```

### 2. Установка Docker

#### Ubuntu/Debian:
```bash
# Удаляем старые версии
sudo apt remove docker docker-engine docker.io containerd runc

# Установка зависимостей
sudo apt install apt-transport-https ca-certificates curl gnupg lsb-release

# Добавляем ключ Docker GPG
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Добавляем репозиторий
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Устанавливаем Docker
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Добавляем пользователя в группу docker
sudo usermod -aG docker $USER
```

#### CentOS/RHEL:
```bash
# Установка yum-utils
sudo yum install -y yum-utils

# Добавляем репозиторий Docker
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# Устанавливаем Docker
sudo yum install docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Запускаем и включаем автозапуск
sudo systemctl start docker
sudo systemctl enable docker

# Добавляем пользователя в группу docker
sudo usermod -aG docker $USER
```

### 3. Установка Docker Compose (если не установлен)

```bash
# Скачиваем Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Делаем исполняемым
sudo chmod +x /usr/local/bin/docker-compose

# Проверяем установку
docker-compose --version
```

### 4. Установка Git

```bash
# Ubuntu/Debian
sudo apt install git

# CentOS/RHEL
sudo yum install git
```

## 📥 Клонирование проекта

```bash
# Переходим в домашнюю директорию
cd ~

# Клонируем репозиторий
git clone https://github.com/YOUR_USERNAME/telegram-bot-ca-analysis.git

# Переходим в директорию проекта
cd telegram-bot-ca-analysis
```

## ⚙️ Настройка проекта

### 1. Создание .env файла

```bash
# Копируем пример конфигурации
cp env_example .env

# Редактируем конфигурацию
nano .env
```

### 2. Настройка .env файла

**Для одного бота:**
```env
# Основные настройки
BOT_NAME=analiz-ca-bot
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_FROM_BOTFATHER
WEBHOOK_PORT=8080

# Google API
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_DRIVE_FOLDER_ID=YOUR_FOLDER_ID

# N8N
N8N_OUTGOING_WEBHOOK_URL=https://your-n8n.com/webhook/create-sheets

# Webhook'и систем
WEBHOOK_URL_1=https://system1.com/webhook
WEBHOOK_URL_2=https://system2.com/webhook
# ... до WEBHOOK_URL_9
```

**Для нескольких ботов (создать отдельные директории):**

```bash
# Создаем директории для каждого бота
mkdir -p ~/bots/bot1 ~/bots/bot2 ~/bots/bot3

# Копируем проект в каждую директорию
cp -r ~/telegram-bot-ca-analysis/* ~/bots/bot1/
cp -r ~/telegram-bot-ca-analysis/* ~/bots/bot2/
cp -r ~/telegram-bot-ca-analysis/* ~/bots/bot3/
```

**bot1/.env:**
```env
BOT_NAME=analiz-ca-bot
WEBHOOK_PORT=8080
TELEGRAM_BOT_TOKEN=bot1_token
```

**bot2/.env:**
```env
BOT_NAME=support-bot
WEBHOOK_PORT=8081
TELEGRAM_BOT_TOKEN=bot2_token
```

**bot3/.env:**
```env
BOT_NAME=sales-bot
WEBHOOK_PORT=8082
TELEGRAM_BOT_TOKEN=bot3_token
```

### 3. Добавление credentials.json

```bash
# Создаем файл credentials.json
nano credentials.json

# Вставляем JSON содержимое файла Google Service Account
# Получить можно в Google Cloud Console -> IAM -> Service Accounts
```

Пример credentials.json:
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "service-account@project.iam.gserviceaccount.com",
  "client_id": "client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token"
}
```

## 🚀 Запуск ботов

### Один бот

```bash
# Переходим в директорию проекта
cd ~/telegram-bot-ca-analysis

# Запускаем бота
./scripts/start.sh

# Проверяем статус
./scripts/status.sh

# Смотрим логи
./scripts/logs.sh
```

### Несколько ботов

```bash
# Запуск каждого бота в своей директории
cd ~/bots/bot1 && ./scripts/start.sh
cd ~/bots/bot2 && ./scripts/start.sh
cd ~/bots/bot3 && ./scripts/start.sh

# Проверка статуса всех ботов
docker ps

# Проверка портов
netstat -tulpn | grep -E "8080|8081|8082"
```

## 🔥 Настройка фаервола

### Ubuntu/Debian (ufw)

```bash
# Включаем фаервол
sudo ufw enable

# Открываем SSH
sudo ufw allow ssh

# Открываем порты для ботов
sudo ufw allow 8080/tcp comment "Bot 1 webhooks"
sudo ufw allow 8081/tcp comment "Bot 2 webhooks"
sudo ufw allow 8082/tcp comment "Bot 3 webhooks"

# Проверяем статус
sudo ufw status
```

### CentOS/RHEL (firewalld)

```bash
# Запускаем firewalld
sudo systemctl start firewalld
sudo systemctl enable firewalld

# Открываем порты
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --permanent --add-port=8081/tcp
sudo firewall-cmd --permanent --add-port=8082/tcp

# Перезагружаем правила
sudo firewall-cmd --reload

# Проверяем
sudo firewall-cmd --list-ports
```

## 🔄 Автозапуск при перезагрузке сервера

### Systemd сервисы

Создаем systemd сервис для каждого бота:

```bash
# Создаем сервис для бота 1
sudo nano /etc/systemd/system/telegram-bot-1.service
```

**Содержимое файла:**
```ini
[Unit]
Description=Telegram Bot 1 - CA Analysis
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/username/bots/bot1
ExecStart=/home/username/bots/bot1/scripts/start.sh
ExecStop=/home/username/bots/bot1/scripts/stop.sh
TimeoutStartSec=0
User=username
Group=username

[Install]
WantedBy=multi-user.target
```

```bash
# Заменяем username на ваше имя пользователя
sudo sed -i 's/username/YOUR_USERNAME/g' /etc/systemd/system/telegram-bot-1.service

# Перезагружаем systemd
sudo systemctl daemon-reload

# Включаем автозапуск
sudo systemctl enable telegram-bot-1.service

# Запускаем сервис
sudo systemctl start telegram-bot-1.service

# Проверяем статус
sudo systemctl status telegram-bot-1.service
```

Повторяем для других ботов (telegram-bot-2.service, telegram-bot-3.service).

## 📊 Мониторинг

### Проверка статуса ботов

```bash
# Статус Docker контейнеров
docker ps

# Статус через systemd
sudo systemctl status telegram-bot-1.service

# Логи в реальном времени
cd ~/bots/bot1 && ./scripts/logs.sh

# Проверка health check
curl http://localhost:8080/health
curl http://localhost:8081/health
curl http://localhost:8082/health
```

### Мониторинг ресурсов

```bash
# Использование ресурсов контейнерами
docker stats

# Использование портов
netstat -tulpn | grep -E "8080|8081|8082"

# Логи системы
journalctl -u telegram-bot-1.service -f
```

## 🛠️ Управление ботами

### Команды для каждого бота

```bash
# Переходим в директорию бота
cd ~/bots/bot1

# Запуск
./scripts/start.sh

# Остановка
./scripts/stop.sh

# Перезапуск
./scripts/restart.sh

# Логи
./scripts/logs.sh

# Статус
./scripts/status.sh
```

### Массовые операции

**Скрипт для управления всеми ботами:**

```bash
# Создаем скрипт управления
nano ~/manage-all-bots.sh
```

```bash
#!/bin/bash

BOT_DIRS=("$HOME/bots/bot1" "$HOME/bots/bot2" "$HOME/bots/bot3")
ACTION=$1

if [ -z "$ACTION" ]; then
    echo "Использование: $0 [start|stop|restart|status|logs]"
    exit 1
fi

for BOT_DIR in "${BOT_DIRS[@]}"; do
    if [ -d "$BOT_DIR" ]; then
        echo "=== Обработка $BOT_DIR ==="
        cd "$BOT_DIR"
        
        case $ACTION in
            "start")
                ./scripts/start.sh
                ;;
            "stop")
                ./scripts/stop.sh
                ;;
            "restart")
                ./scripts/restart.sh
                ;;
            "status")
                ./scripts/status.sh
                ;;
            "logs")
                echo "Логи для $BOT_DIR (нажмите Ctrl+C для следующего бота):"
                ./scripts/logs.sh
                ;;
            *)
                echo "Неизвестная команда: $ACTION"
                ;;
        esac
        echo ""
    fi
done
```

```bash
# Делаем исполняемым
chmod +x ~/manage-all-bots.sh

# Использование
~/manage-all-bots.sh start    # Запуск всех ботов
~/manage-all-bots.sh stop     # Остановка всех ботов
~/manage-all-bots.sh status   # Статус всех ботов
```

## 🔐 Безопасность

### 1. Обновления

```bash
# Регулярно обновляем систему
sudo apt update && sudo apt upgrade -y

# Обновляем Docker образы
cd ~/bots/bot1 && docker-compose pull && ./scripts/restart.sh
```

### 2. Резервное копирование

```bash
# Создаем бэкап конфигураций
tar -czf ~/backup-$(date +%Y%m%d).tar.gz ~/bots/

# Бэкап в другое место
scp ~/backup-$(date +%Y%m%d).tar.gz user@backup-server:/backups/
```

### 3. Мониторинг логов

```bash
# Настройка logrotate для больших логов
sudo nano /etc/logrotate.d/telegram-bots
```

```
/home/username/bots/*/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    notifempty
    copytruncate
}
```

## 🚨 Устранение неполадок

### Проблемы с запуском

```bash
# Проверяем Docker
sudo systemctl status docker

# Проверяем права доступа
ls -la ~/bots/bot1/scripts/

# Проверяем .env файл
cat ~/bots/bot1/.env

# Проверяем credentials.json
ls -la ~/bots/bot1/credentials.json
```

### Проблемы с портами

```bash
# Проверяем какие порты заняты
netstat -tulpn | grep :8080

# Убиваем процессы на порту
sudo fuser -k 8080/tcp
```

### Проблемы с Docker

```bash
# Перезапуск Docker
sudo systemctl restart docker

# Очистка неиспользуемых образов
docker system prune -f

# Просмотр логов Docker
sudo journalctl -u docker.service
```

## ✅ Проверка развертывания

После развертывания проверьте:

1. **Боты отвечают**: отправьте `/start` каждому боту
2. **Health check работает**: `curl http://localhost:8080/health`
3. **Webhook'и доступны**: проверьте внешние URL
4. **Логи пишутся**: `./scripts/logs.sh`
5. **Автозапуск работает**: перезагрузите сервер и проверьте

🎉 **Поздравляем! Ваши Telegram боты успешно развернуты!**
