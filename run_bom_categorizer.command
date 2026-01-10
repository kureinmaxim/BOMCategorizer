#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# BOM Categorizer - macOS Launcher
# ═══════════════════════════════════════════════════════════════════════════════
# Этот скрипт запускает BOM Categorizer из виртуального окружения
# Для использования: двойной клик на файл в Finder или запуск из терминала
# ═══════════════════════════════════════════════════════════════════════════════

cd "$(dirname "$0")"

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  🚀 BOM Categorizer - Запуск${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Активируем виртуальное окружение
if [ -d "venv" ]; then
    echo -e "${GREEN}✓ Активация виртуального окружения (venv)...${NC}"
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo -e "${GREEN}✓ Активация виртуального окружения (.venv)...${NC}"
    source .venv/bin/activate
else
    echo -e "${RED}❌ Ошибка: Виртуальное окружение не найдено!${NC}"
    echo -e "${YELLOW}Создайте его командой: python3 -m venv venv${NC}"
    echo ""
    read -p "Нажмите Enter для выхода..."
    exit 1
fi

# Проверяем наличие зависимостей
if ! python -c "import PySide6" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  PySide6 не установлен. Устанавливаем зависимости...${NC}"
    pip install -r requirements.txt
fi

# Запускаем приложение
echo -e "${GREEN}✓ Запуск BOM Categorizer Modern Edition...${NC}"
echo ""
python app_qt.py

# Держим окно открытым при ошибке
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo -e "${RED}❌ Приложение завершилось с ошибкой (код: $EXIT_CODE)${NC}"
    read -p "Нажмите Enter для выхода..."
fi
