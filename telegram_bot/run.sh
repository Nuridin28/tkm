#!/bin/bash

# Запуск Telegram бота

# Проверка наличия .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден!"
    echo "Скопируйте .env.example в .env и заполните необходимые переменные"
    exit 1
fi

# Проверка токена бота
if ! grep -q "TELEGRAM_BOT_TOKEN=" .env || grep -q "TELEGRAM_BOT_TOKEN=your_bot_token" .env; then
    echo "❌ TELEGRAM_BOT_TOKEN не настроен в .env"
    echo "Получите токен у @BotFather в Telegram"
    exit 1
fi

# Проверяем и останавливаем старые процессы бота
OLD_BOT_PIDS=$(ps aux | grep "[p]ython3.*bot.py" | grep -v grep | awk '{print $2}')
if [ ! -z "$OLD_BOT_PIDS" ]; then
    echo "⚠ Найдены запущенные экземпляры бота. Останавливаю..."
    for pid in $OLD_BOT_PIDS; do
        kill $pid 2>/dev/null && echo "  → Остановлен процесс PID: $pid"
    done
    sleep 2
fi

# Также проверяем процессы через PID файл (если используется)
PID_FILE="/tmp/telecom_bots/telegram.pid"
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE" 2>/dev/null)
    if [ ! -z "$OLD_PID" ] && ps -p $OLD_PID > /dev/null 2>&1; then
        echo "⚠ Найден процесс по PID файлу. Останавливаю..."
        kill $OLD_PID 2>/dev/null
        rm -f "$PID_FILE"
        sleep 2
    fi
fi

echo "🚀 Запуск Telegram бота..."

# Активируем виртуальное окружение если оно существует
if [ -d "venv" ]; then
    echo "📦 Активация виртуального окружения..."
    source venv/bin/activate
fi

python3 bot.py

