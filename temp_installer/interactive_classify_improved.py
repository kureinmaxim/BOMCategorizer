#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Улучшенный интерактивный классификатор BOM файлов
Запуск: python interactive_classify_improved.py --input "БЗ.doc"
"""

import os
import sys
import json
import argparse
import pandas as pd
from typing import List, Dict, Any

# Исправление кодировки для корректного вывода русских символов
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from split_bom import (
    parse_docx, parse_txt_like, normalize_column_names, 
    find_column, classify_row, has_any
)


def load_rules(rules_path: str = "rules.json") -> List[Dict[str, Any]]:
    """Загрузка существующих правил"""
    if os.path.exists(rules_path):
        try:
            with open(rules_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Не удалось загрузить правила: {e}")
    return []


def save_rules(rules: List[Dict[str, Any]], rules_path: str = "rules.json"):
    """Сохранение правил"""
    try:
        with open(rules_path, "w", encoding="utf-8") as f:
            json.dump(rules, f, ensure_ascii=False, indent=2)
        print(f"✅ Правила сохранены в {rules_path}")
    except Exception as e:
        print(f"❌ Не удалось сохранить правила: {e}")


def get_category_display() -> List[tuple]:
    """Возвращает список категорий для отображения"""
    return [
        ("resistors", "Резисторы"),
        ("capacitors", "Конденсаторы"),
        ("inductors", "Дроссели/Катушки"),
        ("ics", "Микросхемы"),
        ("connectors", "Разъемы"),
        ("dev_boards", "Отладочные платы"),
        ("optics", "Оптические компоненты"),
        ("rf_modules", "СВЧ модули"),
        ("cables", "Кабели"),
        ("power_modules", "Модули питания"),
        ("diods", "Диоды/Индикаторы"),
        ("our_developments", "Наши разработки"),
        ("others", "Другие компоненты"),
        ("skip", "⏭️  Пропустить этот элемент"),
    ]


def interactive_classify(input_file: str, output_file: str = "categorized.xlsx", 
                         rules_path: str = "rules.json", sheets: str = None):
    """Интерактивная классификация с автоматическим созданием правил"""
    
    print("\n" + "="*80)
    print("🔍 ИНТЕРАКТИВНЫЙ КЛАССИФИКАТОР BOM ФАЙЛОВ")
    print("="*80)
    print(f"📁 Входной файл: {input_file}")
    print(f"📄 Выходной файл: {output_file}")
    print(f"📋 Файл правил: {rules_path}")
    print("="*80 + "\n")
    
    # Загрузка данных
    ext = os.path.splitext(input_file)[1].lower()
    
    if ext == ".txt":
        df = parse_txt_like(input_file)
    elif ext == ".docx":
        df = parse_docx(input_file)
    elif ext == ".doc":
        # Попытка конвертации через Word COM
        try:
            from win32com.client import Dispatch
            word = Dispatch("Word.Application")
            word.Visible = False
            doc = word.Documents.Open(os.path.abspath(input_file))
            tmp_docx = os.path.splitext(os.path.abspath(input_file))[0] + "_conv_temp.docx"
            doc.SaveAs(tmp_docx, FileFormat=12)  # wdFormatXMLDocument
            doc.Close(False)
            word.Quit()
            df = parse_docx(tmp_docx)
            os.remove(tmp_docx)
        except Exception:
            print("⚠️  Не удалось конвертировать .doc, пробую как текст...")
            df = parse_txt_like(input_file)
    else:  # xlsx
        df = pd.read_excel(input_file, engine="openpyxl")
    
    # Нормализация колонок
    original_cols = list(df.columns)
    lower_cols = normalize_column_names(original_cols)
    rename_map = {orig: norm for orig, norm in zip(original_cols, lower_cols)}
    df = df.rename(columns=rename_map)
    
    # Найти колонки
    ref_col = find_column(["ref", "reference", "designator", "обозначение", "позиционное обозначение"], list(df.columns))
    desc_col = find_column(["description", "desc", "наименование", "имя", "item", "part name"], list(df.columns))
    value_col = find_column(["value", "значение", "номинал"], list(df.columns))
    part_col = find_column(["partnumber", "mfr part", "mpn", "pn", "art", "артикул", "part"], list(df.columns))
    
    # Первичная классификация
    print("⏳ Выполняю первичную классификацию...\n")
    categories = []
    for _, row in df.iterrows():
        ref = row.get(ref_col) if ref_col else None
        desc = row.get(desc_col) if desc_col else None
        val = row.get(value_col) if value_col else None
        part = row.get(part_col) if part_col else None
        categories.append(classify_row(ref, desc, val, part, strict=True))
    
    df["category"] = categories
    
    # Фильтруем неклассифицированные
    unclassified = df[df["category"] == "unclassified"].copy()
    
    if len(unclassified) == 0:
        print("✅ Все элементы успешно классифицированы автоматически!")
        return
    
    print(f"📊 Статистика первичной классификации:")
    print(f"   ✅ Классифицировано: {len(df) - len(unclassified)}")
    print(f"   ❓ Требует уточнения: {len(unclassified)}")
    print("\n" + "="*80 + "\n")
    
    # Загружаем существующие правила
    rules = load_rules(rules_path)
    cat_display = get_category_display()
    
    # Интерактивная обработка
    new_rules_count = 0
    
    for idx, (df_idx, row) in enumerate(unclassified.iterrows(), start=1):
        ref = row.get(ref_col) if ref_col else ""
        desc = row.get(desc_col) if desc_col else ""
        val = row.get(value_col) if value_col else ""
        part = row.get(part_col) if part_col else ""
        
        # Формируем описание для отображения
        display_parts = []
        if pd.notna(ref) and str(ref).strip():
            display_parts.append(f"[{ref}]")
        if pd.notna(desc) and str(desc).strip():
            display_parts.append(str(desc))
        if pd.notna(val) and str(val).strip():
            display_parts.append(f"(Знач: {val})")
        
        display_text = " ".join(display_parts)
        if not display_text.strip():
            continue  # Пропускаем пустые строки
        
        print(f"\n{'─'*80}")
        print(f"Элемент {idx} из {len(unclassified)}:")
        print(f"{'─'*80}")
        print(f"📝 {display_text[:150]}")
        print(f"{'─'*80}")
        print("\nВыберите категорию:")
        
        for i, (cat_key, cat_name) in enumerate(cat_display, start=1):
            print(f"  {i:2d}. {cat_name}")
        
        print("\n  0. ❌ Оставить нераспределенным")
        print("  q. 🚪 Выйти и сохранить")
        
        while True:
            try:
                choice = input("\n👉 Ваш выбор: ").strip().lower()
                
                if choice == "q":
                    print("\n💾 Сохраняю результаты...")
                    if new_rules_count > 0:
                        save_rules(rules, rules_path)
                    return
                
                if choice == "" or choice == "0":
                    print("⏭️  Пропущено")
                    break
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(cat_display):
                    selected_cat = cat_display[choice_num - 1][0]
                    
                    if selected_cat == "skip":
                        print("⏭️  Пропущено")
                        break
                    
                    # Обновляем категорию
                    df.loc[df_idx, "category"] = selected_cat
                    
                    # Создаем правило на основе описания
                    rule_text = str(desc)[:100] if pd.notna(desc) else ""
                    if rule_text.strip():
                        # Проверяем, нет ли уже такого правила
                        rule_exists = any(
                            rule.get("contains", "").lower() in rule_text.lower() or
                            rule_text.lower() in rule.get("contains", "").lower()
                            for rule in rules
                        )
                        
                        if not rule_exists:
                            new_rule = {
                                "contains": rule_text.strip(),
                                "category": selected_cat
                            }
                            rules.append(new_rule)
                            new_rules_count += 1
                            print(f"✅ Правило создано! (всего новых правил: {new_rules_count})")
                        else:
                            print(f"✅ Категория назначена (правило уже существует)")
                    else:
                        print(f"✅ Категория назначена")
                    
                    break
                else:
                    print("❌ Неверный выбор, попробуйте снова")
            except ValueError:
                print("❌ Введите число от 0 до {}, или 'q' для выхода".format(len(cat_display)))
            except KeyboardInterrupt:
                print("\n\n⚠️  Прервано пользователем")
                if new_rules_count > 0:
                    save_rules(rules, rules_path)
                return
    
    print("\n" + "="*80)
    print("🎉 Интерактивная классификация завершена!")
    print("="*80)
    print(f"✅ Новых правил создано: {new_rules_count}")
    
    if new_rules_count > 0:
        save_rules(rules, rules_path)
    
    # Сохраняем результат
    print(f"\n💾 Сохраняю результаты в {output_file}...")
    
    # Здесь нужно запустить полную обработку с новыми правилами
    print("\n🔄 Запускаю полную обработку с новыми правилами...")
    print("   Используйте команду:")
    print(f"   python split_bom.py --inputs \"{input_file}\" --xlsx \"{output_file}\" --assign-json \"{rules_path}\" --combine")


def main():
    parser = argparse.ArgumentParser(
        description="Улучшенный интерактивный классификатор BOM файлов",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python interactive_classify_improved.py --input "example/БЗ.doc"
  python interactive_classify_improved.py --input "example/bom.xlsx" --output result.xlsx
  python interactive_classify_improved.py --input "bom.xlsx" --rules custom_rules.json
        """
    )
    
    parser.add_argument("--input", required=True, help="Путь к входному файлу (XLSX/DOC/DOCX/TXT)")
    parser.add_argument("--output", default="categorized.xlsx", help="Путь к выходному XLSX файлу")
    parser.add_argument("--rules", default="rules.json", help="Путь к файлу с правилами (по умолчанию: rules.json)")
    parser.add_argument("--sheets", help="Номера/имена листов для XLSX (например: 3,4)")
    
    args = parser.parse_args()
    
    try:
        interactive_classify(args.input, args.output, args.rules, args.sheets)
    except KeyboardInterrupt:
        print("\n\n👋 До свидания!")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

