### Создание инсталлятора (.exe) с Inno Setup

Требования
- Windows 10/11
- Установлен Python 3.10+ (на машине разработчика)
- Inno Setup Compiler (ISCC) установлен и добавлен в PATH

Файлы проекта (обязательные)
- `installer.iss` — скрипт Inno Setup (уже подготовлен)
- `post_install.ps1` — пост‑инсталляционный скрипт (создаёт `.venv`, ставит зависимости)
- `requirements.txt` — зависимости Python
- `app.py`, `split_bom.py`, `config.json`, прочие файлы проекта

Версия приложения
- Укажите версию в `config.json` → `app_info.version`.
- Заголовок окна и инсталлятор берут версию из `config.json`.

Сборка через GUI
1) Откройте `installer.iss` в Inno Setup Compiler.
2) Нажмите Compile (F9).
3) В каталоге проекта появится `BOMCategorizerSetup.exe` (см. `OutputDir` в `installer.iss`).

Сборка через командную строку
```powershell
cd C:\Project\ProjectSnabjenie
ISCC.exe installer.iss
```
Если `ISCC.exe` не в PATH, укажите полный путь, например:
`"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss`

Что делает инсталлятор
- Копирует файлы проекта в `{pf64}\BOMCategorizer`.
- Запускает `post_install.ps1` (PowerShell, `-ExecutionPolicy Bypass`):
  - Создаёт `.venv` в `{app}`
  - Обновляет `pip`
  - Устанавливает зависимости из `requirements.txt` (или минимальный набор, если файла нет)
- Создаёт ярлык «BOM Categorizer» в меню Пуск, запускающий `app.py` через `{app}\.venv\Scripts\python.exe`.

Тестирование установки
1) Запустите `BOMCategorizerSetup.exe`.
2) Откройте ярлык «BOM Categorizer» из меню Пуск.
3) Проверьте загрузку GUI, разбор примеров в `example\`.

Тихая установка (для админов/CI)
```powershell
BOMCategorizerSetup.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /LOG=install.log
```

Удаление
- Пуск → «Uninstall BOM Categorizer» (создаётся инсталлятором)
или
```powershell
"C:\Program Files\BOMCategorizer\unins000.exe" /VERYSILENT
```

Подпись (опционально)
- Подпишите `BOMCategorizerSetup.exe` через `signtool` после сборки или добавьте шаг подписи в Inno Setup (см. `SignTool` в документации Inno Setup 6).

Замечания
- При первой установке может занять время из‑за формирования `.venv` и установки зависимостей.
- Для машин без установленного Python пользователю ничего делать не нужно — приложение использует свой `.venv` внутри `{app}`.


