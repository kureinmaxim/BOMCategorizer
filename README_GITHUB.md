# 🎯 BOM Categorizer - Подготовка для GitHub
# 🎯 BOM Categorizer - GitHub Publishing Guide

**Разработчик / Developer:** Куреин М.Н. / Kurein M.N.  
**Дата / Date:** 07.11.2025  
**Версия / Version:** 3.1.3

## 📋 Checklist перед публикацией / Pre-publishing Checklist

### ✅ Выполнено:

1. **Удалены тестовые файлы:**
   - ❌ `quick_test.py` - тестовый скрипт
   - ❌ `ANALYSIS_PROJECT.md` - внутренний анализ

2. **Изменен пароль по умолчанию:**
   - ✅ Пароль изменен с `5421` на `1234` во всех файлах:
     - `config.json`
     - `temp_installer/config.json`
     - `README.md`
     - `bom_categorizer/gui.py`
     - `docs/QUICK_START.md`

3. **Создан `.gitignore`:**
   - Исключены executable файлы (*.exe)
   - Исключены личные данные (database_backups/, component_database.json)
   - Исключены примеры (example/)
   - Исключены временные файлы (temp_installer/)
   - Исключены кэши Python (__pycache__/)

4. **Объединены changelog файлы:**
   - ✅ Создан единый `CHANGELOG.md` из `CHANGELOG_3.0.0.md` и `CHANGELOG_3.1.2.md`

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
- ✅ Документация (docs/, README.md)
- ✅ Правила классификации (rules.json)
- ✅ Конфигурация с дефолтным паролем (config.json)
- ✅ Скрипты установки и управления (*.bat, *.ps1, *.py)
- ✅ Инсталлятор конфигурация (installer_clean.iss)
- ✅ Зависимости (requirements.txt, offline_packages/)
- ✅ Тесты (tests/)
- ✅ Changelog (CHANGELOG.md)

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
   - Приложите `BOMCategorizerSetup.exe` к релизу (не в репозиторий!)
   - Укажите версию из `config.json` (3.1.3)

### 🚀 Первый push на GitHub:

```bash
# Создайте новый репозиторий на GitHub (без README, без .gitignore)
# Затем выполните:

git remote add origin https://github.com/ваш-username/BOMCategorizer.git
git branch -M main
git push -u origin main

# Создайте первый релиз на GitHub:
# 1. Перейдите в "Releases" -> "Create a new release"
# 2. Tag version: v3.1.3
# 3. Release title: BOM Categorizer v3.1.3
# 4. Приложите файл: BOMCategorizerSetup.exe
# 5. Опишите изменения из CHANGELOG.md
```

### ⚠️ ВАЖНО перед push:

1. **Проверьте дважды что пароль изменен:**
   ```bash
   grep -r "5421" . --exclude-dir=.git
   # Не должно быть результатов!
   ```

2. **Убедитесь что БД не попадет в репозиторий:**
   ```bash
   git ls-files | grep component_database
   # Не должно быть результатов!
   ```

3. **Проверьте .gitignore:**
   ```bash
   git status --ignored
   # Должны быть ignored: example/, database_backups/, *.exe
   ```

### 📧 Контакты:

**Разработчик:** Куреин М.Н.  
**Версия:** 3.1.3  
**Дата:** 07.11.2025

---

**Готово к публикации на GitHub!** 🎉

