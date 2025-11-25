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
cp requirements.txt "${PORTABLE_DIR}/requirements.txt"
cp -r bom_categorizer "${PORTABLE_DIR}/"

# Создаем launcher скрипт
cat > "${PORTABLE_DIR}/BOM Categorizer.command" << 'EOF'
#!/bin/bash
# Launcher для BOM Categorizer

# Получаем директорию скрипта
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# ⚠️ ВАЖНО: Проверяем, что приложение НЕ запущено с DMG или read-only диска
if [[ "$DIR" == /Volumes/* ]]; then
    osascript -e 'display dialog "⚠️ ОШИБКА ЗАПУСКА!\n\nВы пытаетесь запустить приложение прямо с DMG образа.\n\nПОРЯДОК УСТАНОВКИ:\n1. Откройте DMG (уже открыт)\n2. СКОПИРУЙТЕ папку \"BOM_Categorizer_Portable\" в:\n   • Документы\n   • Рабочий стол\n   • Или любое другое место\n3. Запустите приложение из скопированной папки\n\nПриложение НЕ МОЖЕТ работать с read-only диска!" buttons {"Понятно"} default button "Понятно" with icon caution with title "BOM Categorizer"'
    exit 1
fi

# Проверка возможности записи
if [ ! -w "$DIR" ]; then
    osascript -e 'display dialog "⚠️ ОШИБКА ДОСТУПА!\n\nПапка приложения защищена от записи.\n\nСкопируйте папку в место с правами записи:\n• Документы\n• Рабочий стол\n• Домашняя папка" buttons {"OK"} default button "OK" with icon stop with title "BOM Categorizer"'
    exit 1
fi

cd "$DIR"

# Проверяем наличие Python 3
if ! command -v python3 &> /dev/null; then
    osascript -e 'display dialog "❌ Python 3 не установлен!\n\nУстановите Python 3.8+ с:\nhttps://www.python.org/downloads/\n\nПосле установки запустите приложение снова." buttons {"OK"} default button "OK" with icon stop with title "BOM Categorizer"'
    open "https://www.python.org/downloads/"
    exit 1
fi

# Проверяем наличие виртуального окружения
if [ ! -d "venv" ]; then
    osascript -e 'display dialog "🚀 Первый запуск!\n\nСейчас будут установлены необходимые компоненты.\n\nЭто займет 1-2 минуты и требует интернет." buttons {"Продолжить"} default button "Продолжить" with icon note with title "BOM Categorizer"'
    
    # Создаем виртуальное окружение
    python3 -m venv venv || {
        osascript -e 'display dialog "❌ Ошибка создания виртуального окружения!\n\nПроверьте права доступа к папке." buttons {"OK"} default button "OK" with icon stop'
        exit 1
    }
    
    source venv/bin/activate
    pip install --upgrade pip > /dev/null 2>&1
    pip install -r requirements.txt > /dev/null 2>&1 || {
        osascript -e 'display dialog "❌ Ошибка установки зависимостей!\n\nПроверьте интернет-соединение." buttons {"OK"} default button "OK" with icon stop'
        exit 1
    }
    
    osascript -e 'display dialog "✅ Установка завершена!\n\nПриложение запустится сейчас." buttons {"OK"} default button "OK" with icon note with title "BOM Categorizer"'
fi

# Активируем виртуальное окружение и запускаем приложение
source venv/bin/activate
python3 app.py

# Деактивируем окружение
deactivate 2>/dev/null
EOF

# Делаем launcher исполняемым
chmod +x "${PORTABLE_DIR}/BOM Categorizer.command"

# Создаем README
cat > "${PORTABLE_DIR}/README.txt" << EOF
╔════════════════════════════════════════════════════════════╗
║   BOM Categorizer v${VERSION} для macOS                   ║
╚════════════════════════════════════════════════════════════╝

⚠️  ВАЖНО: СНАЧАЛА СКОПИРУЙТЕ ПАПКУ!

ПОРЯДОК УСТАНОВКИ:
═══════════════════

1. ✅ Убедитесь, что Python 3.8+ установлен
   Скачать: https://www.python.org/downloads/

2. 📂 СКОПИРУЙТЕ папку "BOM_Categorizer_Portable" в:
   • Документы
   • Рабочий стол  
   • Или любое другое место (НЕ DMG!)

3. 🚀 Запустите "BOM Categorizer.command" (двойной клик)
   При первом запуске установятся зависимости (1-2 минуты)

⚠️ НЕ ЗАПУСКАЙТЕ ПРЯМО С DMG!
Приложение не может работать с read-only диска.


ЕСЛИ macOS БЛОКИРУЕТ ЗАПУСК:
═══════════════════════════

Системные настройки → Конфиденциальность и безопасность
→ "Открыть в любом случае"


АЛЬТЕРНАТИВНЫЙ ЗАПУСК (Терминал):
═══════════════════════════════════

cd "путь/к/BOM_Categorizer_Portable"
python3 app.py


СИСТЕМНЫЕ ТРЕБОВАНИЯ:
════════════════════

✓ macOS 10.13 или новее
✓ Python 3.8+
✓ Интернет (для первого запуска)


ТЕХПОДДЕРЖКА:
════════════

GitHub: https://github.com/kureinmaxim/BOMCategorizer

────────────────────────────────────────────────────────────
Разработчик: $(python3 -c "import json; print(json.load(open('config.json'))['app_info']['developer'])")
Версия: ${VERSION}
Дата: $(date '+%d.%m.%Y')
────────────────────────────────────────────────────────────
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

