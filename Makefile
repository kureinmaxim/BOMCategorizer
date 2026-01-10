# ═══════════════════════════════════════════════════════════════════════════════
# BOM Categorizer - Makefile
# ═══════════════════════════════════════════════════════════════════════════════
#
# Использование:
#   make help              - Показать справку
#   make version-status    - Показать текущую версию
#   make version-sync      - Синхронизировать версию во всех файлах
#   make version-bump-patch - 1.0.0 → 1.0.1
#   make version-bump-minor - 1.0.0 → 1.1.0
#   make version-bump-major - 1.0.0 → 2.0.0
#   make version-set v=X.Y.Z - Установить конкретную версию
#   make build-macos       - Собрать macOS DMG
#
# ═══════════════════════════════════════════════════════════════════════════════

# Переменные
PYTHON := python3
TOOLS_DIR := tools
VERSION_SCRIPT := $(TOOLS_DIR)/update_version.py

# Определяем ОС
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
    # macOS
    VENV_ACTIVATE := source venv/bin/activate
else ifeq ($(UNAME_S),Linux)
    # Linux
    VENV_ACTIVATE := source venv/bin/activate
else
    # Windows (Git Bash/MSYS)
    VENV_ACTIVATE := source venv/Scripts/activate
endif

# ═══════════════════════════════════════════════════════════════════════════════
# Справка
# ═══════════════════════════════════════════════════════════════════════════════

.PHONY: help
help:
	@echo ""
	@echo "════════════════════════════════════════════════════════════════"
	@echo "📦 BOM Categorizer - Makefile"
	@echo "════════════════════════════════════════════════════════════════"
	@echo ""
	@echo "🔧 Управление версиями:"
	@echo "  make version-status       Показать текущую версию"
	@echo "  make version-sync         Синхронизировать версию"
	@echo "  make version-bump-patch   1.0.0 → 1.0.1"
	@echo "  make version-bump-minor   1.0.0 → 1.1.0"
	@echo "  make version-bump-major   1.0.0 → 2.0.0"
	@echo "  make version-set v=X.Y.Z  Установить версию"
	@echo ""
	@echo "🚀 Запуск:"
	@echo "  make run                  Запустить Standard Edition (Tkinter)"
	@echo "  make run-qt               Запустить Modern Edition (PySide6)"
	@echo ""
	@echo "📦 Сборка:"
	@echo "  make build-macos          Собрать macOS DMG инсталлятор"
	@echo "  make build-windows        Собрать Windows инсталлятор"
	@echo ""
	@echo "🧪 Тестирование:"
	@echo "  make test                 Запустить тесты"
	@echo ""
	@echo "🧹 Очистка:"
	@echo "  make clean                Очистить временные файлы"
	@echo ""

# ═══════════════════════════════════════════════════════════════════════════════
# Управление версиями
# ═══════════════════════════════════════════════════════════════════════════════

.PHONY: version-status
version-status:
	@$(PYTHON) $(VERSION_SCRIPT) status

.PHONY: version-sync
version-sync:
	@$(PYTHON) $(VERSION_SCRIPT) sync

.PHONY: version-bump-patch
version-bump-patch:
	@$(PYTHON) $(VERSION_SCRIPT) bump patch

.PHONY: version-bump-minor
version-bump-minor:
	@$(PYTHON) $(VERSION_SCRIPT) bump minor

.PHONY: version-bump-major
version-bump-major:
	@$(PYTHON) $(VERSION_SCRIPT) bump major

.PHONY: version-set
version-set:
ifndef v
	@echo "❌ Укажите версию: make version-set v=X.Y.Z"
else
	@$(PYTHON) $(VERSION_SCRIPT) sync $(v)
endif

# ═══════════════════════════════════════════════════════════════════════════════
# Запуск приложения
# ═══════════════════════════════════════════════════════════════════════════════

.PHONY: run
run:
	@echo "🚀 Запуск BOM Categorizer Standard Edition..."
	@$(PYTHON) app.py

.PHONY: run-qt
run-qt:
	@echo "🚀 Запуск BOM Categorizer Modern Edition..."
	@$(PYTHON) app_qt.py

# ═══════════════════════════════════════════════════════════════════════════════
# Сборка
# ═══════════════════════════════════════════════════════════════════════════════

.PHONY: build-macos
build-macos:
	@echo "📦 Сборка macOS DMG инсталлятора..."
	@bash deployment/build_macos.sh

.PHONY: build-windows
build-windows:
	@echo "📦 Сборка Windows инсталлятора..."
	@$(PYTHON) deployment/build_installer.py

# ═══════════════════════════════════════════════════════════════════════════════
# Тестирование
# ═══════════════════════════════════════════════════════════════════════════════

.PHONY: test
test:
	@echo "🧪 Запуск тестов..."
	@$(PYTHON) run_tests.py

# ═══════════════════════════════════════════════════════════════════════════════
# Очистка
# ═══════════════════════════════════════════════════════════════════════════════

.PHONY: clean
clean:
	@echo "🧹 Очистка временных файлов..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf htmlcov/ .coverage 2>/dev/null || true
	@echo "✅ Очистка завершена"

# ═══════════════════════════════════════════════════════════════════════════════
# Установка зависимостей
# ═══════════════════════════════════════════════════════════════════════════════

.PHONY: install
install:
	@echo "📦 Установка зависимостей..."
	@pip install -r requirements.txt

.PHONY: install-dev
install-dev:
	@echo "📦 Установка dev зависимостей..."
	@pip install -r requirements.txt
	@pip install pytest ruff mypy

# ═══════════════════════════════════════════════════════════════════════════════
# По умолчанию
# ═══════════════════════════════════════════════════════════════════════════════

.DEFAULT_GOAL := help
