# -*- coding: utf-8 -*-
"""
Утилита для проверки доступности шрифтов с поддержкой кириллицы для PDF экспорта
"""

import os
import platform


def check_font_availability():
    """Проверяет доступность шрифтов с поддержкой кириллицы"""
    
    print("=" * 70)
    print("Проверка шрифтов для PDF экспорта с поддержкой кириллицы")
    print("=" * 70)
    print(f"\nОперационная система: {platform.system()} {platform.release()}")
    print()
    
    system = platform.system()
    fonts_found = []
    fonts_missing = []
    
    # Проверяем Arial (Windows/macOS)
    if system == 'Windows':
        arial_paths = {
            'Arial': 'C:/Windows/Fonts/arial.ttf',
            'Arial Bold': 'C:/Windows/Fonts/arialbd.ttf',
        }
        
        print("Проверка Arial:")
        all_exist = True
        for name, path in arial_paths.items():
            exists = os.path.exists(path)
            status = "✓ НАЙДЕН" if exists else "✗ НЕ НАЙДЕН"
            print(f"  {status}: {name} ({path})")
            if exists:
                fonts_found.append(name)
            else:
                fonts_missing.append(name)
                all_exist = False
        
        if all_exist:
            # Пробуем зарегистрировать
            try:
                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont
                pdfmetrics.registerFont(TTFont('Arial', arial_paths['Arial']))
                pdfmetrics.registerFont(TTFont('Arial-Bold', arial_paths['Arial Bold']))
                print("  ✓ УСПЕШНО ЗАРЕГИСТРИРОВАНЫ")
            except Exception as e:
                print(f"  ✗ ОШИБКА РЕГИСТРАЦИИ: {e}")
        print()
    
    elif system == 'Darwin':
        arial_paths = {
            'Arial': '/System/Library/Fonts/Supplemental/Arial.ttf',
            'Arial Bold': '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
        }
        
        print("Проверка Arial:")
        all_exist = True
        for name, path in arial_paths.items():
            exists = os.path.exists(path)
            status = "✓ НАЙДЕН" if exists else "✗ НЕ НАЙДЕН"
            print(f"  {status}: {name} ({path})")
            if exists:
                fonts_found.append(name)
            else:
                fonts_missing.append(name)
                all_exist = False
        
        if all_exist:
            try:
                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont
                pdfmetrics.registerFont(TTFont('Arial', arial_paths['Arial']))
                pdfmetrics.registerFont(TTFont('Arial-Bold', arial_paths['Arial Bold']))
                print("  ✓ УСПЕШНО ЗАРЕГИСТРИРОВАНЫ")
            except Exception as e:
                print(f"  ✗ ОШИБКА РЕГИСТРАЦИИ: {e}")
        print()
    
    # Проверяем DejaVu Sans
    dejavu_paths = {
        'DejaVuSans': [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',  # Linux
            'C:/Windows/Fonts/DejaVuSans.ttf',  # Windows
            '/System/Library/Fonts/DejaVuSans.ttf',  # macOS
        ],
        'DejaVuSans-Bold': [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            'C:/Windows/Fonts/DejaVuSans-Bold.ttf',
            '/System/Library/Fonts/DejaVuSans-Bold.ttf',
        ]
    }
    
    print("Проверка DejaVu Sans:")
    dejavu_found = {}
    for font_name, paths in dejavu_paths.items():
        found_path = next((p for p in paths if os.path.exists(p)), None)
        dejavu_found[font_name] = found_path
        
        if found_path:
            print(f"  ✓ НАЙДЕН: {font_name}")
            print(f"    Путь: {found_path}")
            fonts_found.append(font_name)
        else:
            print(f"  ✗ НЕ НАЙДЕН: {font_name}")
            print(f"    Проверенные пути: {', '.join(paths)}")
            fonts_missing.append(font_name)
    
    if all(dejavu_found.values()):
        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            pdfmetrics.registerFont(TTFont('DejaVuSans', dejavu_found['DejaVuSans']))
            pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', dejavu_found['DejaVuSans-Bold']))
            print("  ✓ УСПЕШНО ЗАРЕГИСТРИРОВАНЫ")
        except Exception as e:
            print(f"  ✗ ОШИБКА РЕГИСТРАЦИИ: {e}")
    print()
    
    # Проверяем DejaVu в папке reportlab
    print("Проверка DejaVu Sans в папке reportlab:")
    try:
        import reportlab
        reportlab_dir = os.path.dirname(reportlab.__file__)
        fonts_dir = os.path.join(reportlab_dir, 'fonts')
        
        reportlab_paths = {
            'DejaVuSans': [
                os.path.join(fonts_dir, 'DejaVuSans.ttf'),
                os.path.join(reportlab_dir, 'lib', 'fonts', 'DejaVuSans.ttf'),
            ],
            'DejaVuSans-Bold': [
                os.path.join(fonts_dir, 'DejaVuSans-Bold.ttf'),
                os.path.join(reportlab_dir, 'lib', 'fonts', 'DejaVuSans-Bold.ttf'),
            ]
        }
        
        reportlab_found = {}
        for font_name, paths in reportlab_paths.items():
            found_path = next((p for p in paths if os.path.exists(p)), None)
            reportlab_found[font_name] = found_path
            
            if found_path:
                print(f"  ✓ НАЙДЕН: {font_name}")
                print(f"    Путь: {found_path}")
                fonts_found.append(f"{font_name} (reportlab)")
            else:
                print(f"  ✗ НЕ НАЙДЕН: {font_name}")
        
        if all(reportlab_found.values()):
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            pdfmetrics.registerFont(TTFont('DejaVuSans', reportlab_found['DejaVuSans']))
            pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', reportlab_found['DejaVuSans-Bold']))
            print("  ✓ УСПЕШНО ЗАРЕГИСТРИРОВАНЫ")
            
    except Exception as e:
        print(f"  ✗ ОШИБКА: {e}")
    print()
    
    # Проверяем Times New Roman для Windows
    if system == 'Windows':
        times_paths = {
            'Times New Roman': 'C:/Windows/Fonts/times.ttf',
            'Times New Roman Bold': 'C:/Windows/Fonts/timesbd.ttf',
        }
        
        print("Проверка Times New Roman:")
        all_exist = True
        for name, path in times_paths.items():
            exists = os.path.exists(path)
            status = "✓ НАЙДЕН" if exists else "✗ НЕ НАЙДЕН"
            print(f"  {status}: {name} ({path})")
            if exists:
                fonts_found.append(name)
            else:
                fonts_missing.append(name)
                all_exist = False
        
        if all_exist:
            try:
                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont
                pdfmetrics.registerFont(TTFont('TimesNewRoman', times_paths['Times New Roman']))
                pdfmetrics.registerFont(TTFont('TimesNewRoman-Bold', times_paths['Times New Roman Bold']))
                print("  ✓ УСПЕШНО ЗАРЕГИСТРИРОВАНЫ")
            except Exception as e:
                print(f"  ✗ ОШИБКА РЕГИСТРАЦИИ: {e}")
        print()
    
    # Итоговый отчет
    print("=" * 70)
    print("ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 70)
    
    if fonts_found:
        print(f"\n✓ Найдено рабочих шрифтов: {len(fonts_found)}")
        print("  Кириллица в PDF должна отображаться корректно!")
    else:
        print("\n✗ НЕ НАЙДЕНО НИ ОДНОГО РАБОЧЕГО ШРИФТА!")
        print("  Кириллица в PDF будет отображаться некорректно (квадратиками).")
    
    if fonts_missing:
        print(f"\n✗ Отсутствуют шрифты: {len(fonts_missing)}")
    
    print("\n" + "=" * 70)
    print("РЕКОМЕНДАЦИИ ПО УСТАНОВКЕ")
    print("=" * 70)
    
    if system == 'Windows':
        print("""
1. Скачайте шрифты DejaVu Sans:
   • Перейдите на https://dejavu-fonts.github.io/
   • Скачайте последнюю версию (dejavu-fonts-ttf-X.XX.zip)
   • Распакуйте архив

2. Установите шрифты:
   • Найдите файлы DejaVuSans.ttf и DejaVuSans-Bold.ttf
   • Скопируйте их в папку C:\\Windows\\Fonts\\
   • Или: щелкните правой кнопкой → "Установить"

3. Перезапустите программу BOMCategorizer

АЛЬТЕРНАТИВНЫЙ СПОСОБ:
   • Установите пакет: pip install reportlab[rlpycairo]
   • Это может добавить шрифты в папку reportlab
""")
    
    elif system == 'Darwin':
        print("""
1. Установите шрифты DejaVu через Homebrew:
   brew tap homebrew/cask-fonts
   brew install --cask font-dejavu

2. Или скачайте вручную:
   • https://dejavu-fonts.github.io/
   • Установите через Font Book

3. Перезапустите программу BOMCategorizer
""")
    
    else:  # Linux
        print("""
1. Установите шрифты через пакетный менеджер:
   
   Ubuntu/Debian:
   sudo apt-get install fonts-dejavu fonts-dejavu-core
   
   Fedora/RHEL:
   sudo dnf install dejavu-sans-fonts
   
   Arch Linux:
   sudo pacman -S ttf-dejavu

2. Перезапустите программу BOMCategorizer
""")
    
    print("=" * 70)
    print("\nНажмите Enter для выхода...")
    input()


if __name__ == '__main__':
    check_font_availability()

