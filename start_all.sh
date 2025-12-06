#!/bin/bash

# Скрипт для запуска всего проекта (Backend, Frontend, Telegram Bot, WhatsApp Bot)
# Использование: ./start_all.sh [options]
# Опции:
#   --no-bots      - запустить только backend и frontend
#   --no-frontend  - запустить только backend и боты
#   --no-backend   - не запускать backend (если уже запущен отдельно)

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Флаги
NO_BOTS=false
NO_FRONTEND=false
NO_BACKEND=false

# Парсинг аргументов
for arg in "$@"; do
    case $arg in
        --no-bots)
            NO_BOTS=true
            shift
            ;;
        --no-frontend)
            NO_FRONTEND=true
            shift
            ;;
        --no-backend)
            NO_BACKEND=true
            shift
            ;;
        *)
            ;;
    esac
done

# PID процессов
BACKEND_PID=""
FRONTEND_PID=""
TELEGRAM_BOT_PID=""
WHATSAPP_BOT_PID=""

# Функция для очистки процессов при выходе
cleanup() {
    echo -e "\n${YELLOW}🛑 Остановка всех процессов...${NC}"
    [ ! -z "$BACKEND_PID" ] && kill $BACKEND_PID 2>/dev/null
    [ ! -z "$FRONTEND_PID" ] && kill $FRONTEND_PID 2>/dev/null
    [ ! -z "$TELEGRAM_BOT_PID" ] && kill $TELEGRAM_BOT_PID 2>/dev/null
    [ ! -z "$WHATSAPP_BOT_PID" ] && kill $WHATSAPP_BOT_PID 2>/dev/null
    echo -e "${GREEN}✓ Все процессы остановлены${NC}"
    exit 0
}

# Установка обработчика сигналов
trap cleanup SIGINT SIGTERM

echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════╗"
echo "║     🚀 Запуск ИИ Help Desk System                     ║"
echo "╚════════════════════════════════════════════════════════╝"
echo -e "${NC}\n"

# Проверка наличия необходимых директорий
if [ ! -d "backend" ]; then
    echo -e "${RED}❌ Директория backend не найдена!${NC}"
    exit 1
fi

if [ ! -d "frontend" ]; then
    echo -e "${RED}❌ Директория frontend не найдена!${NC}"
    exit 1
fi

# ============================================
# 1. BACKEND
# ============================================
if [ "$NO_BACKEND" = false ]; then
    echo -e "${BLUE}📦 Запуск Backend (FastAPI)...${NC}"
    
    if [ ! -d "backend/venv" ]; then
        echo -e "${YELLOW}⚠ Виртуальное окружение не найдено. Создаю...${NC}"
        cd backend
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        cd ..
    fi
    
    cd backend
    source venv/bin/activate
    
    # Проверка .env файла
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}⚠ Файл .env не найден!${NC}"
        echo -e "${YELLOW}  Создайте файл backend/.env с необходимыми переменными${NC}"
    fi
    
    echo -e "${GREEN}  → Backend запускается на http://localhost:8000${NC}"
    echo -e "${GREEN}  → API документация: http://localhost:8000/docs${NC}"
    uvicorn main:app --reload --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
    BACKEND_PID=$!
    cd ..
    
    sleep 3
    if ps -p $BACKEND_PID > /dev/null; then
        echo -e "${GREEN}✓ Backend запущен (PID: $BACKEND_PID)${NC}\n"
    else
        echo -e "${RED}❌ Ошибка запуска Backend. Проверьте backend.log${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⏭ Пропуск Backend (--no-backend)${NC}\n"
fi

# ============================================
# 2. FRONTEND
# ============================================
if [ "$NO_FRONTEND" = false ]; then
    echo -e "${BLUE}🎨 Запуск Frontend (Vite + React)...${NC}"
    
    cd frontend
    
    # Проверка node_modules
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}⚠ Зависимости не установлены. Устанавливаю...${NC}"
        npm install
    fi
    
    # Проверка .env файла
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}⚠ Файл .env не найден!${NC}"
        echo -e "${YELLOW}  Создайте файл frontend/.env с необходимыми переменными${NC}"
    fi
    
    echo -e "${GREEN}  → Frontend запускается на http://localhost:5173${NC}"
    npm run dev > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ..
    
    sleep 2
    if ps -p $FRONTEND_PID > /dev/null; then
        echo -e "${GREEN}✓ Frontend запущен (PID: $FRONTEND_PID)${NC}\n"
    else
        echo -e "${YELLOW}⚠ Возможна ошибка запуска Frontend. Проверьте frontend.log${NC}\n"
    fi
else
    echo -e "${YELLOW}⏭ Пропуск Frontend (--no-frontend)${NC}\n"
fi

# ============================================
# 3. TELEGRAM BOT
# ============================================
if [ "$NO_BOTS" = false ] && [ -d "telegram_bot" ]; then
    echo -e "${BLUE}🤖 Запуск Telegram Bot...${NC}"
    
    # Проверяем и останавливаем старые процессы бота
    OLD_BOT_PIDS=$(ps aux | grep "[p]ython3.*bot.py" | grep -v grep | awk '{print $2}')
    if [ ! -z "$OLD_BOT_PIDS" ]; then
        echo -e "${YELLOW}⚠ Найдены запущенные экземпляры бота. Останавливаю...${NC}"
        for pid in $OLD_BOT_PIDS; do
            kill $pid 2>/dev/null && echo -e "${GREEN}  → Остановлен процесс PID: $pid${NC}"
        done
        sleep 2
    fi
    
    # Также проверяем процессы через PID файл (если используется)
    PID_FILE="/tmp/telecom_bots/telegram.pid"
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE" 2>/dev/null)
        if [ ! -z "$OLD_PID" ] && ps -p $OLD_PID > /dev/null 2>&1; then
            echo -e "${YELLOW}⚠ Найден процесс по PID файлу. Останавливаю...${NC}"
            kill $OLD_PID 2>/dev/null
            rm -f "$PID_FILE"
            sleep 2
        fi
    fi
    
    if [ ! -d "telegram_bot/venv" ]; then
        echo -e "${YELLOW}⚠ Виртуальное окружение не найдено. Создаю...${NC}"
        cd telegram_bot
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        cd ..
    fi
    
    cd telegram_bot
    source venv/bin/activate
    
    # Проверка .env файла
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}⚠ Файл .env не найден!${NC}"
        echo -e "${YELLOW}  Создайте файл telegram_bot/.env с TELEGRAM_BOT_TOKEN${NC}"
    fi
    
    python3 bot.py > ../telegram_bot.log 2>&1 &
    TELEGRAM_BOT_PID=$!
    cd ..
    
    sleep 2
    if ps -p $TELEGRAM_BOT_PID > /dev/null; then
        echo -e "${GREEN}✓ Telegram Bot запущен (PID: $TELEGRAM_BOT_PID)${NC}\n"
    else
        echo -e "${YELLOW}⚠ Возможна ошибка запуска Telegram Bot. Проверьте telegram_bot.log${NC}\n"
    fi
fi

# ============================================
# 4. WHATSAPP BOT
# ============================================
if [ "$NO_BOTS" = false ] && [ -d "whatsapp_bot" ]; then
    echo -e "${BLUE}💬 Запуск WhatsApp Bot...${NC}"
    
    cd whatsapp_bot
    
    # Проверка node_modules
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}⚠ Зависимости не установлены. Устанавливаю...${NC}"
        npm install
    fi
    
    # Проверка .env файла
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}⚠ Файл .env не найден!${NC}"
        echo -e "${YELLOW}  Создайте файл whatsapp_bot/.env с необходимыми переменными${NC}"
    fi
    
    node bot.js > ../whatsapp_bot.log 2>&1 &
    WHATSAPP_BOT_PID=$!
    cd ..
    
    sleep 2
    if ps -p $WHATSAPP_BOT_PID > /dev/null; then
        echo -e "${GREEN}✓ WhatsApp Bot запущен (PID: $WHATSAPP_BOT_PID)${NC}\n"
    else
        echo -e "${YELLOW}⚠ Возможна ошибка запуска WhatsApp Bot. Проверьте whatsapp_bot.log${NC}\n"
    fi
fi

# ============================================
# Итоговая информация
# ============================================
echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════╗"
echo "║                    ✅ Все запущено!                    ║"
echo "╚════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${GREEN}📍 Доступные сервисы:${NC}"
[ "$NO_BACKEND" = false ] && echo -e "  ${GREEN}•${NC} Backend API:     ${CYAN}http://localhost:8000${NC}"
[ "$NO_BACKEND" = false ] && echo -e "  ${GREEN}•${NC} API Docs:        ${CYAN}http://localhost:8000/docs${NC}"
[ "$NO_FRONTEND" = false ] && echo -e "  ${GREEN}•${NC} Frontend:        ${CYAN}http://localhost:5173${NC}"
[ "$NO_BOTS" = false ] && [ ! -z "$TELEGRAM_BOT_PID" ] && echo -e "  ${GREEN}•${NC} Telegram Bot:    ${CYAN}Запущен${NC}"
[ "$NO_BOTS" = false ] && [ ! -z "$WHATSAPP_BOT_PID" ] && echo -e "  ${GREEN}•${NC} WhatsApp Bot:    ${CYAN}Запущен${NC}"

echo -e "\n${YELLOW}📋 Логи:${NC}"
[ "$NO_BACKEND" = false ] && echo -e "  • Backend:        ${CYAN}tail -f backend.log${NC}"
[ "$NO_FRONTEND" = false ] && echo -e "  • Frontend:       ${CYAN}tail -f frontend.log${NC}"
[ "$NO_BOTS" = false ] && [ ! -z "$TELEGRAM_BOT_PID" ] && echo -e "  • Telegram Bot:   ${CYAN}tail -f telegram_bot.log${NC}"
[ "$NO_BOTS" = false ] && [ ! -z "$WHATSAPP_BOT_PID" ] && echo -e "  • WhatsApp Bot:   ${CYAN}tail -f whatsapp_bot.log${NC}"

echo -e "\n${YELLOW}⏹  Для остановки нажмите Ctrl+C${NC}\n"

# Ожидание завершения процессов
wait

