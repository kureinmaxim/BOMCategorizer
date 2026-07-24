# Design: UX встроенного GUI CLI

**Date:** 2026-07-24  
**Status:** Approved (approach B)  
**Scope:** `bom_categorizer/cli_interactive.py` + новый helper `bom_categorizer/cli_ux.py`

## Goal

Улучшить взаимодействие пользователя со встроенной CLI-консолью (кнопка «💻 CLI» в Modern Edition): понятные ошибки, удобный ввод, читаемый вид под текущую тему — без полного редизайна и без новых бизнес-команд.

## Non-goals

- Новые команды обработки BOM / AI / версий
- Рефакторинг всех существующих handlers «ради красоты»
- Терминальный `split_bom.py` / `bom_categorizer.main`
- Полная перепись документации `docs/CLI_USAGE.md` (допускается краткое обновление после)

## Approach

**B — helper + UX в виджете**

| Файл | Ответственность |
|------|-----------------|
| `bom_categorizer/cli_ux.py` | Парсинг строки (`shlex`), fuzzy-подсказки команд, палитры light/dark, утилиты usage |
| `bom_categorizer/cli_interactive.py` | Виджет, регистрация команд, применение палитры, вызов helper при ошибках/вводе |
| `tests/test_cli_ux.py` | Юнит-тесты helper (парсинг, fuzzy, без Qt) |

## Behavior

### 1. Errors & hints

- Неизвестная команда → сообщение + до 3 вариантов `Возможно, вы имели в виду: …` (нормализованное расстояние Левенштейна / общий префикс; порог разумный, например расстояние ≤ 2 или prefix match).
- Ошибка аргументов в handler → если результат/исключение связано с usage, печатать `Использование: {cmd.usage}` и при наличии короткий пример.
- Общий `help` — компактный список по категориям (имя, алиасы, одна строка описания).
- `help <cmd>` — описание, usage, алиасы, пример (если задан).

### 2. Input

- Разбор командной строки через `shlex.split(..., posix=False)` на Windows-совместимом режиме (или эквивалент с поддержкой кавычек), чтобы `add "C:\My Files\bom.xlsx"` работал.
- При ошибке `shlex` — понятное сообщение («проверьте кавычки»), не traceback в UI.
- Tab / completer:
  - имена команд и алиасы (как сейчас);
  - для известных команд — статический список аргументов-подсказок (`theme` → `dark`/`light`, `aiprovider` → `telegram`/`anthropic`/`openai`, и т.п.).
- История ↑↓: без смены модели; после выполнения индекс сбрасывается (уже есть) — убедиться, что после accept completion история не ломается.

### 3. Appearance

- Палитра зависит от `main_window.current_theme` (`dark` / `light`): фон вывода, поле ввода, prompt, цвета success/error/hint/command.
- Welcome короче: название, версия, 2–3 строки подсказок (help / Tab / ↑↓), без «плывущих» пробелов в ASCII-рамке.
- Семантика цветов едина: команда пользователя, успех, ошибка, нейтральная подсказка.

### 4. Optional examples on CLICommand

Расширить `CLICommand` опциональным полем `example: str = ""` для `help <cmd>` и сообщений об ошибках. Заполнить для ключевых команд (`add`, `remove`, `theme`, `scale`, `dbsearch`, `aiprovider`, `aimodel`) — не обязательно для всех.

## Theme bug note (in scope if cheap)

`theme dark|light` сейчас вызывает `toggle_theme()` без проверки текущего значения — может переключить «не туда». В рамках UX: выставлять запрошенную тему явно (если API есть) или toggle только когда текущая ≠ запрошенной.

## Testing

- Unit: `cli_ux` — split с кавычками, fuzzy suggestions, palette keys.
- Ручная проверка в GUI: light/dark, `add` с пробелом в пути, опечатка команды, `help`, Tab.

## Risks

- `shlex` на Windows с `\` в путях — нужен `posix=False` и smoke-тесты.
- Большой `cli_interactive.py` — менять точечно, не переносить все handlers в helper.
