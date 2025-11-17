"""
Модуль для управления конфигурационными файлами
"""
import os
import shutil
import json


def initialize_config_from_template(config_name="config.json"):
    """
    Инициализирует конфиг из шаблона при первом запуске.
    
    Args:
        config_name: Имя конфига (config.json или config_qt.json)
    
    Returns:
        bool: True если конфиг был создан, False если уже существовал
    """
    # Определяем пути
    base_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(base_dir)
    config_path = os.path.join(parent_dir, config_name)
    template_path = os.path.join(parent_dir, f"{config_name}.template")
    
    # Если конфиг уже есть - ничего не делаем
    if os.path.exists(config_path):
        return False
    
    # Ищем шаблон
    if os.path.exists(template_path):
        # Копируем шаблон
        shutil.copy2(template_path, config_path)
        print(f"✅ Создан конфигурационный файл из шаблона: {config_name}")
        return True
    else:
        # Если шаблона нет - создаем базовый конфиг
        print(f"⚠️  Шаблон не найден: {template_path}")
        print(f"⚠️  Создаю минимальный конфиг: {config_name}")
        
        if "qt" in config_name:
            default_config = {
                "app_info": {
                    "version": "4.4.2",
                    "edition": "Modern Edition",
                    "developer": "Куреин М.Н.",
                    "developer_en": "Kurein M.N."
                },
                "security": {
                    "pin": "1234",
                    "require_pin": True
                },
                "window": {
                    "width": 730,
                    "height": 550,
                    "remember_size": True
                },
                "ui": {
                    "theme": "dark",
                    "font_size": 12,
                    "scale_factor": 1.0,
                    "view_mode": "simple",
                    "log_timestamps": False,
                    "auto_open_output": False,
                    "auto_export_pdf": False,
                    "ai_classifier_enabled": False,
                    "ai_auto_classify": False
                }
            }
        else:
            default_config = {
                "app_info": {
                    "version": "3.0.0",
                    "edition": "Standard",
                    "developer": "Куреин М.Н.",
                    "developer_en": "Kurein M.N."
                },
                "security": {
                    "pin": "1234",
                    "require_pin": True
                },
                "window": {
                    "width": 750,
                    "height": 1110,
                    "remember_size": True
                }
            }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Создан минимальный конфиг: {config_name}")
        return True


def initialize_all_configs():
    """
    Инициализирует все конфигурационные файлы из шаблонов при первом запуске.
    """
    configs = ["config.json", "config_qt.json"]
    created_count = 0
    
    for config_name in configs:
        if initialize_config_from_template(config_name):
            created_count += 1
    
    if created_count > 0:
        print(f"\n✅ Инициализировано конфигов: {created_count}")
    
    return created_count


if __name__ == "__main__":
    # Для тестирования
    initialize_all_configs()

