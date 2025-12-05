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

echo "🚀 Запуск Telegram бота..."

# Активируем виртуальное окружение если оно существует
if [ -d "venv" ]; then
    echo "📦 Активация виртуального окружения..."
    source venv/bin/activate
fi

python3 bot.py

