#!/bin/bash

# Скрипт для остановки всех экземпляров Telegram бота

echo "🛑 Остановка Telegram бота..."

# Останавливаем процессы через ps
OLD_BOT_PIDS=$(ps aux | grep "[p]ython3.*bot.py" | grep -v grep | awk '{print $2}')
if [ ! -z "$OLD_BOT_PIDS" ]; then
    echo "Найдены запущенные экземпляры бота:"
    for pid in $OLD_BOT_PIDS; do
        echo "  → Останавливаю процесс PID: $pid"
        kill $pid 2>/dev/null
    done
    sleep 2
    
    # Проверяем, остались ли процессы
    REMAINING=$(ps aux | grep "[p]ython3.*bot.py" | grep -v grep | awk '{print $2}')
    if [ ! -z "$REMAINING" ]; then
        echo "Принудительная остановка оставшихся процессов:"
        for pid in $REMAINING; do
            echo "  → Принудительно останавливаю PID: $pid"
            kill -9 $pid 2>/dev/null
        done
    fi
else
    echo "Запущенные экземпляры бота не найдены."
fi

# Также проверяем процессы через PID файл (если используется)
PID_FILE="/tmp/telecom_bots/telegram.pid"
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE" 2>/dev/null)
    if [ ! -z "$OLD_PID" ] && ps -p $OLD_PID > /dev/null 2>&1; then
        echo "Найден процесс по PID файлу (PID: $OLD_PID). Останавливаю..."
        kill $OLD_PID 2>/dev/null
        sleep 1
        if ps -p $OLD_PID > /dev/null 2>&1; then
            kill -9 $OLD_PID 2>/dev/null
        fi
    fi
    rm -f "$PID_FILE"
fi

echo "✅ Все экземпляры бота остановлены."

