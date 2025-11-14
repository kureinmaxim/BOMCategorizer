# Шрифты для PDF экспорта с поддержкой кириллицы

Эта папка содержит шрифты TrueType для корректного отображения кириллицы в PDF файлах.

## Требуемые файлы

Для работы PDF экспорта необходимы следующие файлы шрифтов DejaVu Sans:

- `DejaVuSans.ttf` - основной шрифт
- `DejaVuSans-Bold.ttf` - жирный шрифт

## Как получить шрифты

### Вариант 1: Скачать с официального сайта

1. Перейдите на https://dejavu-fonts.github.io/
2. Скачайте последнюю версию (например, `dejavu-fonts-ttf-2.37.zip`)
3. Распакуйте архив
4. Найдите файлы:
   - `dejavu-fonts-ttf-2.37/ttf/DejaVuSans.ttf`
   - `dejavu-fonts-ttf-2.37/ttf/DejaVuSans-Bold.ttf`
5. Скопируйте эти файлы в папку `fonts` проекта BOMCategorizer

### Вариант 2: Скачать напрямую из GitHub

```bash
# DejaVuSans.ttf
curl -L -o fonts/DejaVuSans.ttf https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf

# DejaVuSans-Bold.ttf
curl -L -o fonts/DejaVuSans-Bold.ttf https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans-Bold.ttf
```

### Вариант 3: PowerShell скрипт (Windows)

Запустите `download_fonts.ps1` в корне проекта.

## Лицензия

DejaVu fonts являются бесплатными шрифтами с открытым исходным кодом под лицензией DejaVu Fonts License (основана на Bitstream Vera и Arev Fonts License).

Лицензия разрешает:
- ✓ Свободное использование
- ✓ Распространение
- ✓ Модификацию
- ✓ Коммерческое использование

Подробнее: https://dejavu-fonts.github.io/License.html

## Встраивание в инсталлятор

После добавления файлов шрифтов в эту папку:

1. Файлы автоматически будут включены в инсталлятор Inno Setup
2. При установке программы шрифты будут скопированы в `{app}\fonts\`
3. Программа автоматически найдет и использует эти шрифты для PDF экспорта
4. Кириллица будет отображаться корректно на всех машинах

## Проверка

После установки шрифтов запустите:
```bash
python check_pdf_fonts.py
```

Это покажет, какие шрифты доступны для использования в PDF.

## Альтернативные решения

Если не хотите встраивать шрифты в инсталлятор:

1. Пользователи могут установить шрифты вручную в системную папку Windows
2. Программа также пытается использовать системные шрифты Arial и Times New Roman
3. На машинах, где доступны системные кириллические шрифты, PDF будет работать без дополнительных действий

