#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для создания иконок приложения из исходного PNG
Создает .ico для Windows и .icns для macOS
"""

import os
import sys
from pathlib import Path

def create_icons():
    """Создает иконки из icon.png"""
    
    # Проверка наличия исходного файла
    icon_source = Path("icon.png")
    if not icon_source.exists():
        print("❌ Ошибка: Файл icon.png не найден!")
        print("   Сохраните иконку в корень проекта с именем icon.png")
        return False
    
    print("✅ Найден icon.png")
    print()
    
    try:
        from PIL import Image
    except ImportError:
        print("⚠️  Pillow не установлен. Устанавливаю...")
        os.system(f"{sys.executable} -m pip install Pillow")
        from PIL import Image
    
    # Открываем исходное изображение
    img = Image.open(icon_source)
    print(f"📐 Размер исходного изображения: {img.size}")
    
    # === Windows: создаем .ico ===
    print("\n🪟 Создание Windows .ico...")
    
    # Размеры для Windows (несколько размеров в одном .ico)
    win_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    
    # Создаем временные изображения разных размеров
    win_images = []
    for size in win_sizes:
        resized = img.resize(size, Image.Resampling.LANCZOS)
        win_images.append(resized)
    
    # Сохраняем как .ico (все размеры в одном файле)
    ico_path = Path("icon.ico")
    win_images[0].save(
        ico_path,
        format='ICO',
        sizes=win_sizes
    )
    print(f"✅ Создан: {ico_path} ({', '.join([f'{s[0]}x{s[1]}' for s in win_sizes])})")
    
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
        icns_path = Path("icon.icns")
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
    print(f"  • icon.ico  - для Windows (installer_clean.iss, installer_qt.iss)")
    print(f"  • icon.icns - для macOS (setup_macos.py)")
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

