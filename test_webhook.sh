#!/bin/bash

SERVER_IP="46.173.26.60"
PORT="8085"

echo "🔍 Диагностика webhook сервера $SERVER_IP:$PORT"
echo "================================================"

echo -e "\n1️⃣ Проверка доступности порта:"
nc -zv $SERVER_IP $PORT 2>&1

echo -e "\n2️⃣ Проверка Health Check:"
curl -v -X GET http://$SERVER_IP:$PORT/health 2>&1 | head -20

echo -e "\n3️⃣ Тест N8N Webhook endpoint:"
curl -v -X POST http://$SERVER_IP:$PORT/webhook/n8n/spreadsheet \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "test_123",
    "user_id": 123456789,
    "spreadsheet_id": "test_id",
    "spreadsheet_url": "https://docs.google.com/spreadsheets/d/test/edit",
    "sheet_title": "Test Sheet",
    "created_at": "2025-09-20T18:30:00Z",
    "status": "created"
  }' 2>&1 | head -20

echo -e "\n4️⃣ Проверка базового HTTP ответа:"
telnet $SERVER_IP $PORT << EOF
GET / HTTP/1.1
Host: $SERVER_IP
Connection: close

EOF
