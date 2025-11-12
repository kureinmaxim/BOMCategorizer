# -*- coding: utf-8 -*-
"""
Скрипт для слияния базы данных компонентов при обновлении
Вызывается после установки для объединения старой и новой баз
"""

import json
import os
import shutil

def merge_databases():
    """
    Объединяет существующую базу данных пользователя с новой базой из инсталлятора
    """
    db_path = "component_database.json"
    backup_path = "component_database.backup.json"
    
    # Если файл не существует - ничего не делаем (будет создан при первом запуске)
    if not os.path.exists(db_path):
        print("База данных компонентов не найдена - будет создана при первом запуске")
        return
    
    try:
        # Создаем резервную копию
        if os.path.exists(db_path):
            shutil.copy2(db_path, backup_path)
            print(f"✓ Создана резервная копия: {backup_path}")
        
        # Загружаем текущую базу
        with open(db_path, 'r', encoding='utf-8') as f:
            current_db = json.load(f)
        
        print(f"✓ Загружена текущая база: {len(current_db)} записей")
        
        # Если была новая база от инсталлятора (component_database_new.json)
        new_db_path = "component_database_new.json"
        if os.path.exists(new_db_path):
            with open(new_db_path, 'r', encoding='utf-8') as f:
                new_db = json.load(f)
            
            print(f"✓ Найдена новая база от инсталлятора: {len(new_db)} записей")
            
            # Объединяем - приоритет у пользовательской базы
            added_count = 0
            for key, value in new_db.items():
                if key not in current_db:
                    current_db[key] = value
                    added_count += 1
            
            print(f"✓ Добавлено {added_count} новых записей")
            
            # Сохраняем объединенную базу
            with open(db_path, 'w', encoding='utf-8') as f:
                json.dump(current_db, f, ensure_ascii=False, indent=2, sort_keys=True)
            
            print(f"✓ База данных обновлена: {len(current_db)} записей")
            
            # Удаляем временный файл
            os.remove(new_db_path)
        else:
            print("✓ Обновление базы не требуется")
        
    except Exception as e:
        print(f"✗ Ошибка при слиянии баз данных: {e}")
        # В случае ошибки восстанавливаем из резервной копии
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, db_path)
            print(f"✓ База восстановлена из резервной копии")

if __name__ == "__main__":
    merge_databases()

