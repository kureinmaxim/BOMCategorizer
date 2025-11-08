#!/bin/bash
# Скрипт для создания macOS инсталлятора

set -e  # Остановка при ошибке

echo "🚀 Начинаем создание macOS инсталлятора..."

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Получаем версию из config.json
VERSION=$(python3 -c "import json; print(json.load(open('config.json'))['app_info']['version'])")
APP_NAME="BOM Categorizer"
DMG_NAME="BOMCategorizer-${VERSION}-macOS"

echo -e "${BLUE}📦 Версия: ${VERSION}${NC}"

# Проверка виртуального окружения
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Виртуальное окружение не найдено!${NC}"
    echo "Создаем виртуальное окружение..."
    python3 -m venv venv
fi

# Активация виртуального окружения
source venv/bin/activate

# Установка зависимостей для сборки
echo -e "${BLUE}📥 Установка зависимостей для сборки...${NC}"
pip install --upgrade pip
pip install -r requirements_macos.txt
pip install py2app

# Очистка предыдущих сборок
echo -e "${BLUE}🧹 Очистка предыдущих сборок...${NC}"
rm -rf build dist

# Создание .app bundle
echo -e "${BLUE}🔨 Создание .app bundle...${NC}"
python3 setup_macos.py py2app

# Проверка создания .app
if [ ! -d "dist/${APP_NAME}.app" ]; then
    echo -e "${RED}❌ Ошибка: .app bundle не создан!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ .app bundle создан успешно${NC}"

# Создание DMG
echo -e "${BLUE}💿 Создание DMG образа...${NC}"

# Создаем временную папку для DMG
DMG_TEMP="dmg_temp"
rm -rf "${DMG_TEMP}"
mkdir -p "${DMG_TEMP}"

# Копируем приложение
cp -R "dist/${APP_NAME}.app" "${DMG_TEMP}/"

# Создаем символическую ссылку на Applications
ln -s /Applications "${DMG_TEMP}/Applications"

# Создаем README
cat > "${DMG_TEMP}/README.txt" << EOF
${APP_NAME} v${VERSION}

УСТАНОВКА:
Перетащите "${APP_NAME}.app" в папку "Applications"

ЗАПУСК:
1. Откройте Finder
2. Перейдите в Applications
3. Найдите "${APP_NAME}"
4. При первом запуске: 
   - Если система блокирует запуск, откройте:
     Системные настройки → Безопасность и конфиденциальность
   - Нажмите "Открыть в любом случае"

ТРЕБОВАНИЯ:
- macOS 10.13 или новее
- Python 3.8+ (включен в приложение)

Разработчик: $(python3 -c "import json; print(json.load(open('config.json'))['app_info']['developer'])")
Дата релиза: $(python3 -c "import json; print(json.load(open('config.json'))['app_info']['release_date'])")
EOF

# Создаем DMG
echo -e "${BLUE}📀 Упаковка в DMG...${NC}"
hdiutil create -volname "${APP_NAME}" \
    -srcfolder "${DMG_TEMP}" \
    -ov -format UDZO \
    "${DMG_NAME}.dmg"

# Очистка временных файлов
rm -rf "${DMG_TEMP}"

echo -e "${GREEN}✅ DMG создан: ${DMG_NAME}.dmg${NC}"

# Информация о файле
DMG_SIZE=$(du -h "${DMG_NAME}.dmg" | cut -f1)
echo -e "${BLUE}📊 Размер DMG: ${DMG_SIZE}${NC}"

echo ""
echo -e "${GREEN}🎉 Готово!${NC}"
echo -e "${BLUE}📦 Инсталлятор: ${DMG_NAME}.dmg${NC}"
echo -e "${BLUE}📂 .app bundle: dist/${APP_NAME}.app${NC}"
echo ""
echo -e "${BLUE}Для установки:${NC}"
echo "1. Откройте ${DMG_NAME}.dmg"
echo "2. Перетащите '${APP_NAME}' в папку Applications"
echo ""

