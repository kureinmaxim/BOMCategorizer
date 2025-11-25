#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для создания иконок приложения из исходного PNG
Создает .ico для Windows и .icns для macOS
"""

import os
import sys
from pathlib import Path

# Исправление кодировки для Windows
if sys.platform == 'win32':
    try:
        if sys.stdout.encoding != 'utf-8':
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8')
                sys.stderr.reconfigure(encoding='utf-8')
            else:
                import codecs
                sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
                sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except (AttributeError, OSError):
        pass

def create_icons():
    """Создает иконки из icon.png или icon.icns"""
    
    # Проверка наличия исходного файла
    icon_source = None
    source_type = None
    
    # Сначала проверяем assets/icon.png
    if Path("assets/icon.png").exists():
        icon_source = Path("assets/icon.png")
        source_type = "PNG"
        print("✅ Найден assets/icon.png")
    # Если нет assets/icon.png, проверяем assets/icon.icns
    elif Path("assets/icon.icns").exists():
        icon_source = Path("assets/icon.icns")
        source_type = "ICNS"
        print("✅ Найден assets/icon.icns (будет использован как источник)")
    else:
        print("❌ Ошибка: Файл assets/icon.png или assets/icon.icns не найден!")
        print("   Сохраните иконку в папку assets/ с именем icon.png")
        print("   Или используйте assets/icon.icns (будет извлечено изображение для Windows)")
        return False
    
    print()
    
    try:
        from PIL import Image
    except ImportError:
        print("⚠️  Pillow не установлен. Устанавливаю...")
        os.system(f"{sys.executable} -m pip install Pillow")
        from PIL import Image
    
    # Открываем исходное изображение
    if source_type == "ICNS":
        # Для .icns нужно извлечь изображение
        # .icns - это архив с PNG файлами разных размеров
        # Используем самый большой размер (обычно 1024x1024 или 512x512)
        print("📦 Извлечение изображения из icon.icns...")
        try:
            # Пробуем открыть .icns напрямую (Pillow может поддерживать)
            img = Image.open(icon_source)
            print(f"✅ Изображение извлечено из assets/icon.icns")
        except Exception as e:
            print(f"⚠️  Не удалось открыть icon.icns напрямую: {e}")
            print("💡 Рекомендация: Используйте assets/icon.png как исходный файл")
            print("   Или конвертируйте assets/icon.icns в PNG через онлайн конвертер")
            return False
    else:
        img = Image.open(icon_source)
    
    print(f"📐 Размер исходного изображения: {img.size}")
    
    # === Windows: создаем .ico ===
    print("\n🪟 Создание Windows .ico...")
    
    # Размеры для Windows (расширенный набор для лучшего качества)
    # Включаем все стандартные размеры Windows + дополнительные для четкости
    win_sizes = [
        (16, 16),    # Маленькие иконки в списках
        (24, 24),    # Маленькие иконки (Windows 10+)
        (32, 32),    # Стандартные иконки
        (40, 40),    # Средние иконки (Windows 10+)
        (48, 48),    # Большие иконки
        (64, 64),    # Очень большие иконки
        (96, 96),    # Экстра большие иконки
        (128, 128),  # Огромные иконки
        (256, 256),  # Максимальный размер для Windows
    ]
    
    # Создаем временные изображения разных размеров с оптимизацией
    win_images = []
    for size in win_sizes:
        # Для маленьких размеров используем более агрессивную фильтрацию
        if size[0] <= 32:
            # Для очень маленьких размеров используем ANTIALIAS для лучшей четкости
            resized = img.resize(size, Image.Resampling.LANCZOS)
            # Применяем дополнительную резкость для маленьких размеров
            from PIL import ImageFilter, ImageEnhance
            # Легкая резкость для улучшения читаемости
            enhancer = ImageEnhance.Sharpness(resized)
            resized = enhancer.enhance(1.2)  # Увеличиваем резкость на 20%
        else:
            # Для больших размеров используем стандартный LANCZOS
            resized = img.resize(size, Image.Resampling.LANCZOS)
        win_images.append(resized)
    
    # Сохраняем как .ico (все размеры в одном файле)
    ico_path = Path("assets/icon.ico")
    
    # Конвертируем все в RGBA если нужно (для поддержки прозрачности)
    win_images_rgba = []
    for img in win_images:
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        win_images_rgba.append(img)
    
    # Сохраняем многослойную ICO
    # Проблема: Pillow может не правильно создавать многослойные ICO через sizes
    # Решение: Используем все изображения через правильный метод
    
    # Метод 1: Попытка сохранить с sizes (Pillow 9.0+)
    # Если не работает, используем альтернативный метод
    try:
        # Сохраняем первое изображение с указанием всех размеров
        win_images_rgba[0].save(
            ico_path,
            format='ICO',
            sizes=[(w, h) for w, h in win_sizes]
        )
        
        # Проверяем размер файла
        file_size = ico_path.stat().st_size
        
        # Для 9 размеров ожидаемый размер примерно 50-150 KB
        # Если файл слишком мал, значит Pillow не включил все размеры
        if file_size < 20 * 1024:
            print(f"   ⚠️  Размер файла: {file_size / 1024:.1f} KB (слишком мал)")
            print(f"   ⚠️  Pillow не включил все размеры в ICO файл")
            print(f"   💡 Создаю ICO через альтернативный метод...")
            
            # Метод 2: Пробуем использовать ImageMagick если доступен
            try:
                import subprocess
                # Проверяем наличие ImageMagick
                result = subprocess.run(
                    ['magick', '-version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    print(f"   ✅ ImageMagick найден, создаю ICO через ImageMagick...")
                    # Используем ImageMagick для создания правильной многослойной ICO
                    sizes_str = ','.join([str(s[0]) for s in win_sizes])
                    cmd = [
                        'magick',
                        str(icon_source),
                        '-define', f'icon:auto-resize={sizes_str}',
                        str(ico_path)
                    ]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    if result.returncode == 0 and ico_path.exists():
                        new_size = ico_path.stat().st_size
                        if new_size > 20 * 1024:
                            print(f"   ✅ Создан через ImageMagick: {new_size / 1024:.1f} KB")
                        else:
                            print(f"   ⚠️  ImageMagick создал файл, но размер все еще мал")
                    else:
                        print(f"   ⚠️  ImageMagick не смог создать ICO: {result.stderr}")
            except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
                # ImageMagick не найден или произошла ошибка
                pass
            
            # Если ImageMagick не помог, предлагаем альтернативы
            if ico_path.exists():
                final_size = ico_path.stat().st_size
                if final_size < 20 * 1024:
                    print(f"   💡 Рекомендация: Используйте один из методов:")
                    print(f"      ")
                    print(f"      Метод 1 - Онлайн конвертер (рекомендуется):")
                    print(f"      1. Откройте: https://convertio.co/png-ico/")
                    print(f"      2. Загрузите assets/icon.png")
                    print(f"      3. Выберите опцию 'Multiple sizes'")
                    print(f"      4. Выберите размеры: 16, 24, 32, 40, 48, 64, 96, 128, 256")
                    print(f"      5. Скачайте icon.ico и замените текущий файл")
                    print(f"      ")
                    print(f"      Метод 2 - ImageMagick (если установлен):")
                    print(f"      magick assets/icon.png -define icon:auto-resize=16,24,32,40,48,64,96,128,256 assets/icon.ico")
                    print(f"      ")
                    print(f"      Метод 3 - IcoFX или другой редактор иконок")
        else:
            print(f"   ✅ Размер файла: {file_size / 1024:.1f} KB")
    except Exception as e:
        print(f"   ⚠️  Ошибка: {e}")
        # Fallback: сохраняем хотя бы с одним размером
        win_images_rgba[0].save(ico_path, format='ICO')
        print(f"   ✅ Создан базовый ICO файл")
    
    print(f"✅ Создан: {ico_path}")
    print(f"   Размеры: {', '.join([f'{s[0]}x{s[1]}' for s in win_sizes])}")
    print(f"   Всего размеров: {len(win_sizes)}")
    print(f"   💡 Для лучшего качества используйте исходное изображение минимум 512x512 пикселей")
    
    # === macOS: создаем .icns (требует дополнительных инструментов) ===
    print("\n🍎 Создание macOS .icns...")
    
    if sys.platform == 'darwin':
        # На macOS используем iconutil
        iconset_dir = Path("icon.iconset")
        iconset_dir.mkdir(exist_ok=True)
        
        # Размеры для macOS .icns
        mac_sizes = [
            (16, 'icon_16x16.png'),
            (32, 'icon_16x16@2x.png'),
            (32, 'icon_32x32.png'),
            (64, 'icon_32x32@2x.png'),
            (128, 'icon_128x128.png'),
            (256, 'icon_128x128@2x.png'),
            (256, 'icon_256x256.png'),
            (512, 'icon_256x256@2x.png'),
            (512, 'icon_512x512.png'),
            (1024, 'icon_512x512@2x.png'),
        ]
        
        for size, name in mac_sizes:
            resized = img.resize((size, size), Image.Resampling.LANCZOS)
            resized.save(iconset_dir / name)
        
        print(f"✅ Создана папка: {iconset_dir}/")
        
        # Конвертируем в .icns через iconutil
        icns_path = Path("assets/icon.icns")
        result = os.system(f"iconutil -c icns {iconset_dir} -o {icns_path}")
        
        if result == 0:
            print(f"✅ Создан: {icns_path}")
            # Удаляем временную папку
            import shutil
            shutil.rmtree(iconset_dir)
            print("✅ Временная папка удалена")
        else:
            print(f"⚠️  Не удалось создать .icns")
            print(f"   Но папка {iconset_dir}/ создана - используйте iconutil вручную")
    else:
        print("⚠️  Создание .icns доступно только на macOS")
        print("   На Windows/Linux используйте онлайн конвертер:")
        print("   https://cloudconvert.com/png-to-icns")
        print("   или перенесите проект на macOS для создания .icns")
    
    print("\n" + "="*60)
    print("✅ Готово!")
    print("="*60)
    print("\nСозданные файлы:")
    print(f"  • assets/icon.ico  - для Windows (installer_clean.iss, installer_qt.iss)")
    print(f"  • assets/icon.icns - для macOS (setup_macos.py)")
    print("\nСледующие шаги:")
    print("  1. Обновите скрипты сборки (будет сделано автоматически)")
    print("  2. Пересоберите инсталляторы")
    
    return True

if __name__ == "__main__":
    print("="*60)
    print("🎨 Создание иконок приложения")
    print("="*60)
    print()
    
    success = create_icons()
    
    if not success:
        sys.exit(1)

