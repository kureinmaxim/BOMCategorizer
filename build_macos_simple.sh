#!/bin/bash
# Упрощенный скрипт для создания macOS инсталлятора (без py2app)

set -e

echo "🚀 Создание простого macOS инсталлятора..."

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Версия
VERSION=$(python3 -c "import json; print(json.load(open('config.json'))['app_info']['version'])")
APP_NAME="BOMCategorizer"
DMG_NAME="BOMCategorizer-${VERSION}-macOS-Portable"

echo -e "${BLUE}📦 Версия: ${VERSION}${NC}"

# Создаем папку для портативного приложения
PORTABLE_DIR="BOM_Categorizer_Portable"
rm -rf "${PORTABLE_DIR}"
mkdir -p "${PORTABLE_DIR}"

# Копируем все необходимые файлы
echo -e "${BLUE}📋 Копирование файлов...${NC}"
cp app.py "${PORTABLE_DIR}/"
cp config.json "${PORTABLE_DIR}/"
cp requirements_macos.txt "${PORTABLE_DIR}/requirements.txt"
cp -r bom_categorizer "${PORTABLE_DIR}/"

# Создаем launcher скрипт
cat > "${PORTABLE_DIR}/BOM Categorizer.command" << 'EOF'
#!/bin/bash
# Launcher для BOM Categorizer

# Получаем директорию скрипта
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Проверяем наличие Python 3
if ! command -v python3 &> /dev/null; then
    osascript -e 'display dialog "Python 3 не установлен!\n\nУстановите Python 3.8+ с python.org" buttons {"OK"} default button "OK" with icon stop'
    exit 1
fi

# Проверяем наличие виртуального окружения
if [ ! -d "venv" ]; then
    osascript -e 'display dialog "Первый запуск! Установка зависимостей...\n\nЭто может занять несколько минут." buttons {"OK"} default button "OK"'
    
    # Создаем виртуальное окружение
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    osascript -e 'display dialog "Установка завершена! Приложение запустится сейчас." buttons {"OK"} default button "OK"'
fi

# Активируем виртуальное окружение и запускаем приложение
source venv/bin/activate
python3 app.py

# Деактивируем окружение
deactivate
EOF

# Делаем launcher исполняемым
chmod +x "${PORTABLE_DIR}/BOM Categorizer.command"

# Создаем README
cat > "${PORTABLE_DIR}/README.txt" << EOF
BOM Categorizer v${VERSION} для macOS
=====================================

ТРЕБОВАНИЯ:
- macOS 10.13 или новее
- Python 3.8+ (установите с https://www.python.org/)

УСТАНОВКА:
1. Убедитесь, что Python 3 установлен
2. Скопируйте папку "BOM_Categorizer_Portable" в удобное место
3. При первом запуске будут установлены зависимости (требуется интернет)

ЗАПУСК:
Двойной клик на "BOM Categorizer.command"

ПРИМЕЧАНИЕ:
- При первом запуске система может спросить разрешение
- Если macOS блокирует запуск:
  Системные настройки → Безопасность → "Открыть в любом случае"

АЛЬТЕРНАТИВНЫЙ ЗАПУСК (через Терминал):
cd "путь/к/BOM_Categorizer_Portable"
python3 app.py

---
Разработчик: $(python3 -c "import json; print(json.load(open('config.json'))['app_info']['developer'])")
Версия: ${VERSION}
Дата: $(date '+%d.%m.%Y')
EOF

# Создаем DMG
echo -e "${BLUE}💿 Создание DMG...${NC}"
hdiutil create -volname "BOM Categorizer ${VERSION}" \
    -srcfolder "${PORTABLE_DIR}" \
    -ov -format UDZO \
    "${DMG_NAME}.dmg"

# Размер
DMG_SIZE=$(du -h "${DMG_NAME}.dmg" | cut -f1)

echo ""
echo -e "${GREEN}✅ Готово!${NC}"
echo -e "${BLUE}📦 DMG: ${DMG_NAME}.dmg (${DMG_SIZE})${NC}"
echo -e "${BLUE}📁 Портативная версия: ${PORTABLE_DIR}/${NC}"
echo ""
echo -e "${BLUE}Использование:${NC}"
echo "1. Откройте DMG"
echo "2. Скопируйте папку в нужное место"
echo "3. Запустите 'BOM Categorizer.command'"
echo ""
EOF

