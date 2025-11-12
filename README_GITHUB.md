
### 📦 Что нужно сделать перед git push:

```bash
# 1. Добавить .gitignore в git
git add .gitignore

# 2. Добавить объединенный CHANGELOG
git add CHANGELOG.md

# 3. Удалить старые changelog из git (если были добавлены)
git rm --cached CHANGELOG_3.0.0.md CHANGELOG_3.1.2.md 2>/dev/null || true

# 4. Удалить личные данные из индекса git
git rm --cached -r database_backups/ 2>/dev/null || true
git rm --cached component_database.json 2>/dev/null || true
git rm --cached component_database.xlsx 2>/dev/null || true

# 5. Удалить example файлы из индекса
git rm --cached -r example/ 2>/dev/null || true

# 6. Удалить temp_installer из индекса
git rm --cached -r temp_installer/ 2>/dev/null || true

# 7. Удалить тестовые файлы
git rm --cached quick_test.py 2>/dev/null || true
git rm --cached ANALYSIS_PROJECT.md 2>/dev/null || true
git rm --cached temp_for_classification.xlsx 2>/dev/null || true

# 8. Удалить все __pycache__ из индекса
git rm --cached -r bom_categorizer/__pycache__/ 2>/dev/null || true
git rm --cached -r temp_installer/bom_categorizer/__pycache__/ 2>/dev/null || true

# 9. Удалить .exe файлы из индекса
git rm --cached BOMCategorizerSetup.exe 2>/dev/null || true

# 10. Добавить измененные файлы (с новым паролем)
git add config.json README.md bom_categorizer/gui.py docs/QUICK_START.md
git add temp_installer/config.json temp_installer/README.md
git add temp_installer/bom_categorizer/gui.py temp_installer/docs/QUICK_START.md

# 11. Сделать коммит
git commit -m "Подготовка к публикации на GitHub

- Изменен пароль по умолчанию на 1234
- Удалены тестовые файлы и личные данные
- Создан .gitignore для защиты конфиденциальной информации
- Объединены changelog файлы в CHANGELOG.md
- Исключены executable файлы и резервные копии
"

# 12. Проверить что всё правильно
git status
```

### 🔒 Безопасность данных:

**Что ИСКЛЮЧЕНО из репозитория (не будет на GitHub):**

- ❌ Исполняемые файлы (*.exe) - слишком большие и обновляются часто
- ❌ База данных компонентов - может содержать конфиденциальные проекты
- ❌ Резервные копии БД - личная информация
- ❌ Примеры (папка example/) - могут содержать реальные проекты
- ❌ Временные файлы сборки (temp_installer/) - не нужны пользователям
- ❌ Python кэши (__pycache__/) - генерируются автоматически
- ❌ Виртуальное окружение (venv/) - устанавливается локально

**Что ВКЛЮЧЕНО в репозиторий (будет на GitHub):**

- ✅ Исходный код Python (bom_categorizer/)
- ✅ Документация (docs/, README.md, EXPERIMENTAL_FEATURES.md)
- ✅ Правила классификации (rules.json)
- ✅ Конфигурация (config.json, config_qt.json)
- ✅ Скрипты установки и управления (*.bat, *.ps1, *.py)
- ✅ Инсталлятор конфигурация (installer_clean.iss, installer_qt.iss)
- ✅ Зависимости (requirements.txt, offline_packages/)
- ✅ Тесты (tests/)
- ✅ Changelog (CHANGELOG.md)
- ✅ Modern Edition приложение (app_qt.py)
- ✅ Экспериментальные модули (experimental/new-feature ветка)

### 🧪 Экспериментальная ветка:

**Ветка:** `experimental/new-feature`

Содержит новые экспериментальные функции:
- 🎯 **Drag & Drop улучшения** - перетаскивание файлов между панелями, контекстное меню
- 💻 **Интерактивная командная строка** - расширенный CLI режим с автодополнением
- 📄 **Экспорт в PDF** - конвертация выходных файлов в PDF документы
- 🤖 **AI-подсказки** - интеграция с LLM (Claude, GPT, Ollama) для автоматической классификации

**Новые модули:**
- `bom_categorizer/cli_interactive.py`
- `bom_categorizer/drag_drop_qt.py`
- `bom_categorizer/pdf_exporter.py`
- `bom_categorizer/ai_classifier_qt.py`

**Документация:**
- `EXPERIMENTAL_FEATURES.md`
- `docs/DRAG_DROP_README.md`
- `AI_CLASSIFIER_README.md`

### 📝 Дополнительные рекомендации:

1. **Создайте шаблон для примеров:**
   ```bash
   mkdir example_template
   echo "Поместите сюда ваши BOM файлы для тестирования" > example_template/README.md
   git add example_template/
   ```

2. **Добавьте LICENSE:**
   ```bash
   # Например MIT License
   git add LICENSE
   ```

3. **Добавьте CONTRIBUTING.md** (если планируете принимать вклад сообщества)

4. **Создайте GitHub Release:**
   - Приложите `BOMCategorizerModernSetup.exe` к релизу (не в репозиторий!)
   - Укажите версию из `config_qt.json` (4.2.3)

### 🚀 Push на GitHub:

```bash
# Основная ветка (main):
git push origin main

# Экспериментальная ветка:
git push origin experimental/new-feature

# Создайте релиз на GitHub:
# 1. Перейдите в "Releases" -> "Create a new release"
# 2. Tag version: v4.2.3
# 3. Release title: BOM Categorizer Modern Edition v4.2.3
# 4. Приложите файлы:
#    - BOMCategorizerSetup.exe (Classic Edition)
#    - BOMCategorizerModernSetup.exe (Modern Edition)
# 5. Опишите изменения из CHANGELOG.md
# 6. Отметьте экспериментальные функции в описании
```

### ⚠️ ВАЖНО перед push:


1. **Убедитесь что БД не попадет в репозиторий:**
   ```bash
   git ls-files | grep component_database
   # Не должно быть результатов!
   ```

2. **Проверьте .gitignore:**
   ```bash
   git status --ignored
   # Должны быть ignored: example/, database_backups/, *.exe
   ```

### 📧 Контакты:

**Разработчик:** Куреин М.Н.  
**Версия:** 4.2.3  
**Дата:** 12.11.2025

---


