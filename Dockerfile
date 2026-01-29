# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости с оптимизацией
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Настройки для улучшения производительности Python
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONIOENCODING=utf-8

# Настройки для HTTP соединений
ENV HTTPX_POOL_CONNECTIONS=25
ENV HTTPX_POOL_MAXSIZE=25

# Копируем исходный код
COPY *.py ./

# Создаем пользователя для безопасности
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# Открываем порт для webhook'ов
EXPOSE 8080

# Команда запуска
CMD ["python", "bot.py"]
