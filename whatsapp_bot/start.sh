#!/bin/bash

# Скрипт для запуска WhatsApp бота

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🚀 Запуск WhatsApp бота...${NC}\n"

# Проверка установки Node.js
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}❌ Node.js не установлен${NC}"
    echo -e "${YELLOW}Установите Node.js: https://nodejs.org/${NC}"
    exit 1
fi

# Проверка установки зависимостей
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠ Установка зависимостей...${NC}"
    npm install
fi

# Запуск бота
echo -e "${GREEN}✅ Запуск бота...${NC}\n"
npm start

