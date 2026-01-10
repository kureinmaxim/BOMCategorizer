#!/bin/bash
# Скрипт для создания macOS инсталлятора

set -e  # Остановка при ошибке

echo "🚀 Начинаем создание macOS инсталлятора..."

# Переходим в корень проекта
cd "$(dirname "$0")/.." || exit 1

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ========== ДИАЛОГ ВЫБОРА ВЕРСИИ ==========
# Читаем версии из ШАБЛОНОВ config файлов (единственный источник правды)
STANDARD_VERSION=$(python3 -c "import json; print(json.load(open('config/config.json.template'))['app_info']['version'])" 2>/dev/null || echo "3.3.0")
MODERN_VERSION=$(python3 -c "import json; print(json.load(open('config/config_qt.json.template'))['app_info']['version'])" 2>/dev/null || echo "4.2.3")

echo ""
echo -e "${YELLOW}============================================================${NC}"
echo -e "${YELLOW}  ВЫБЕРИТЕ ВЕРСИЮ ДЛЯ СБОРКИ:${NC}"
echo -e "${YELLOW}============================================================${NC}"
echo ""
echo -e "  ${GREEN}[1]${NC} Standard v${STANDARD_VERSION}"
echo -e "      Tkinter GUI (стабильная версия)"
echo -e "      Файл: BOMCategorizer-${STANDARD_VERSION}-macOS-Standard.dmg"
echo ""
echo -e "  ${GREEN}[2]${NC} Modern Edition v${MODERN_VERSION}"
echo -e "      PySide6 GUI (современный дизайн + экспериментальные функции)"
echo -e "      Файл: BOMCategorizer-${MODERN_VERSION}-macOS-Modern.dmg"
echo ""
echo -e "${YELLOW}============================================================${NC}"
echo ""

while true; do
    read -p "Введите номер версии (1 или 2): " EDITION_CHOICE
    case $EDITION_CHOICE in
        1)
            EDITION="Standard"
            CONFIG_FILE="config.json"
            APP_FILE="app.py"
            VERSION="${STANDARD_VERSION}"
            APP_NAME="BOM Categorizer Standard"
            DMG_NAME="BOMCategorizer-${VERSION}-macOS-Standard"
            break
            ;;
        2)
            EDITION="Modern Edition"
            CONFIG_FILE="config_qt.json"
            APP_FILE="app_qt.py"
            VERSION="${MODERN_VERSION}"
            APP_NAME="BOM Categorizer Modern Edition"
            DMG_NAME="BOMCategorizer-${VERSION}-macOS-Modern"
            break
            ;;
        *)
            echo -e "${RED}[ERROR] Неверный выбор. Введите 1 или 2.${NC}"
            ;;
    esac
done

echo ""
echo -e "${GREEN}✓ Выбрана версия: ${EDITION} v${VERSION}${NC}"
echo -e "${BLUE}📦 DMG: ${DMG_NAME}.dmg${NC}"
echo ""

# Синхронизация локального конфига из шаблона перед сборкой
echo -e "${BLUE}🔄 Синхронизация версий перед сборкой...${NC}"

# Принудительная синхронизация всех версий
echo -e "${YELLOW}  Запуск tools/update_version.py sync...${NC}"
if python3 tools/update_version.py sync; then
    echo -e "${GREEN}  ✓ Версии синхронизированы${NC}"
else
    echo -e "${RED}  ❌ Ошибка синхронизации версий!${NC}"
    echo -e "${RED}  Проверьте tools/update_version.py вручную${NC}"
    exit 1
fi

# Проверка версий после синхронизации
echo ""
echo -e "${BLUE}📊 Проверка версий после синхронизации:${NC}"
if [ "$EDITION" = "Standard" ]; then
    SYNCED_VERSION=$(python3 -c "import json; print(json.load(open('config/config.json.template'))['app_info']['version'])" 2>/dev/null)
else
    SYNCED_VERSION=$(python3 -c "import json; print(json.load(open('config/config_qt.json.template'))['app_info']['version'])" 2>/dev/null)
fi
echo -e "${GREEN}  ✓ Версия для сборки: ${SYNCED_VERSION}${NC}"
VERSION="${SYNCED_VERSION}"
DMG_NAME="BOMCategorizer-${VERSION}-macOS-${EDITION// /-}"
echo -e "${BLUE}  📦 DMG файл: ${DMG_NAME}.dmg${NC}"
echo ""

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
pip install -r requirements.txt
pip install py2app

# Очистка предыдущих сборок
echo -e "${BLUE}🧹 Очистка предыдущих сборок...${NC}"
rm -rf build dist *.pyc __pycache__

# Создание .app bundle
echo -e "${BLUE}🔨 Создание .app bundle...${NC}"
echo -e "${YELLOW}Версия: ${EDITION}${NC}"
echo -e "${YELLOW}Конфиг: ${CONFIG_FILE}${NC}"
echo -e "${YELLOW}App файл: ${APP_FILE}${NC}"
echo -e "${YELLOW}Имя приложения: ${APP_NAME}${NC}"
echo ""

# Отключаем автоматическую подпись py2app (для локальной разработки)
export CODESIGN_ALLOCATE="/usr/bin/codesign_allocate"
export PY2APP_CODESIGN=0

if [ "$EDITION" = "Modern Edition" ]; then
    # Modern Edition: исключаем Tkinter, используем только Qt
    echo -e "${GREEN}==> Сборка Modern Edition (PySide6) с параметром --edition=modern${NC}"
    python3 deployment/setup_macos.py py2app --edition=modern 2>&1 | tee deployment/build_py2app.log
    BUILD_EXIT_CODE=$?
else
    echo -e "${GREEN}==> Сборка Standard Edition (Tkinter) БЕЗ параметра edition${NC}"
    python3 deployment/setup_macos.py py2app 2>&1 | tee deployment/build_py2app.log
    BUILD_EXIT_CODE=$?
fi

# Проверка создания .app (главный критерий успеха)
if [ ! -d "dist/${APP_NAME}.app" ]; then
    echo -e "${RED}❌ Ошибка: .app bundle не создан!${NC}"
    echo -e "${RED}Смотрите build_py2app.log для деталей${NC}"
    exit 1
fi

# Если py2app завершился с предупреждениями (обычно из-за missing optional imports)
if [ $BUILD_EXIT_CODE -ne 0 ]; then
    echo -e "${YELLOW}⚠️  py2app завершился с кодом: $BUILD_EXIT_CODE${NC}"
    echo -e "${YELLOW}⚠️  Обычно это предупреждения об опциональных модулях (win32com, matplotlib, и т.д.)${NC}"
    echo -e "${GREEN}📦 Но .app bundle создан успешно!${NC}"
    
    # Проверяем, нужна ли ручная подпись
    if ! codesign -v "dist/${APP_NAME}.app" 2>&1 >/dev/null; then
        echo -e "${BLUE}🔐 Пробуем подписать вручную ad-hoc подписью...${NC}"
        
        if codesign --force --deep --sign - "dist/${APP_NAME}.app" 2>&1; then
            echo -e "${GREEN}✅ Ручная подпись успешна${NC}"
        else
            echo -e "${YELLOW}⚠️  Ручная подпись не удалась${NC}"
            echo -e "${BLUE}ℹ️  Приложение может работать и без подписи на этом Mac${NC}"
            echo -e "${BLUE}ℹ️  Для распространения потребуется правильная подпись${NC}"
        fi
    else
        echo -e "${GREEN}✅ Приложение уже подписано${NC}"
    fi
else
    echo -e "${GREEN}✅ py2app завершился без ошибок${NC}"
fi

echo -e "${GREEN}✅ .app bundle создан успешно${NC}"

# Проверка версии в bundle
echo -e "${BLUE}🔍 Проверка версии в bundle...${NC}"
BUNDLE_CONFIG="dist/${APP_NAME}.app/Contents/Resources/${CONFIG_FILE}"
if [ -f "${BUNDLE_CONFIG}" ]; then
    BUNDLE_VERSION=$(python3 -c "import json; print(json.load(open('${BUNDLE_CONFIG}'))['app_info']['version'])" 2>/dev/null || echo "N/A")
    echo -e "${GREEN}  ✓ Версия в bundle: ${BUNDLE_VERSION}${NC}"
    if [ "${BUNDLE_VERSION}" != "${VERSION}" ]; then
        echo -e "${RED}  ⚠️  ВНИМАНИЕ: Версия в bundle (${BUNDLE_VERSION}) не совпадает с ожидаемой (${VERSION})!${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠️  Конфиг не найден в bundle: ${BUNDLE_CONFIG}${NC}"
fi

# Очистка ненужных GUI файлов после сборки
echo -e "${BLUE}🧹 Очистка ненужных GUI файлов...${NC}"
BOM_CAT_DIR="dist/${APP_NAME}.app/Contents/Resources/bom_categorizer"
if [ "$EDITION" = "Standard" ]; then
    # Для Standard удаляем Qt файлы
    rm -f "$BOM_CAT_DIR/gui_qt.py" "$BOM_CAT_DIR/dialogs_qt.py" 2>/dev/null
    echo -e "${GREEN}  ✓ Удалены: gui_qt.py, dialogs_qt.py${NC}"
else
    # Для Modern Edition удаляем Tkinter GUI (если попал)
    rm -f "$BOM_CAT_DIR/gui.py" 2>/dev/null
    echo -e "${GREEN}  ✓ Tkinter файлы удалены${NC}"
fi

# Переподпись после модификации (иначе macOS убьет приложение)
echo -e "${BLUE}🔐 Переподпись приложения...${NC}"
codesign --remove-signature "dist/${APP_NAME}.app" 2>/dev/null
if codesign --force --deep --sign - "dist/${APP_NAME}.app" 2>&1; then
    echo -e "${GREEN}  ✓ Приложение подписано заново${NC}"
else
    echo -e "${YELLOW}  ⚠️  Подпись не удалась, но попробуем продолжить${NC}"
fi

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

# Создаем README (читаем из шаблона)
DEVELOPER=$(python3 -c "import json; print(json.load(open('config/${CONFIG_FILE}.template'))['app_info']['developer'])")
RELEASE_DATE=$(python3 -c "import json; print(json.load(open('config/${CONFIG_FILE}.template'))['app_info']['release_date'])")

cat > "${DMG_TEMP}/README.txt" << EOF
${APP_NAME} v${VERSION}
${EDITION}

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

Разработчик: ${DEVELOPER}
Дата релиза: ${RELEASE_DATE}
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
echo -e "${YELLOW}Версия: ${EDITION} v${VERSION}${NC}"
echo -e "${BLUE}📦 Инсталлятор: ${DMG_NAME}.dmg${NC}"
echo -e "${BLUE}📂 .app bundle: dist/${APP_NAME}.app${NC}"
echo ""
echo -e "${BLUE}Для установки:${NC}"
echo "1. Откройте ${DMG_NAME}.dmg"
echo "2. Перетащите '${APP_NAME}' в папку Applications"
echo ""

