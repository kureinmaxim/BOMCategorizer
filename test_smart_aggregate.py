#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import pandas as pd

def smart_aggregate_source_file(source_files) -> str:
    """Тестовая версия с отладкой"""
    sources = [str(v) for v in source_files if pd.notna(v) and str(v).strip()]
    if not sources:
        return ''
    
    print(f"  Входные источники: {sources}")
    
    # Извлекаем базовые файлы и пометки
    base_files = set()
    tags = []
    
    for source in sources:
        print(f"  Обрабатываю: '{source}'")
        
        # Паттерн для извлечения базового файла и пометок
        match = re.match(r'^([^,]+?)(?:,\s*(.+))?$', source)
        if match:
            base_file = match.group(1).strip()
            tag = match.group(2)
            
            print(f"    base_file: '{base_file}'")
            print(f"    tag: '{tag}'")
            
            base_files.add(base_file)
            if tag:
                # Извлекаем все пометки типа (п/б ...) или (зам ...)
                tag_matches = re.findall(r'\((п/б|зам)\s+[^)]+\)', tag)
                print(f"    tag_matches: {tag_matches}")
                tags.extend(tag_matches)
    
    print(f"  base_files: {base_files}")
    print(f"  tags: {tags}")
    
    # Если только один базовый файл и есть пометки - компактный формат
    if len(base_files) == 1 and tags:
        base_file = list(base_files)[0]
        unique_tags = []
        seen = set()
        for tag in tags:
            if tag not in seen:
                unique_tags.append(tag)
                seen.add(tag)
        result = f"{base_file}, {', '.join(unique_tags)}"
        print(f"  RESULT: '{result}'")
        return result
    
    # Иначе просто объединяем через запятую
    return ', '.join(sorted(set(sources)))

# Тест
test_sources = pd.Series([
    'Plata_preobrz.docx, (п/б R48*)',
    'Plata_preobrz.docx, (п/б R49*)'
])

print("ТЕСТ 1: Два подбора")
result = smart_aggregate_source_file(test_sources)
print(f"Результат: '{result}'")
print()

# Тест 2
test_sources2 = pd.Series([
    'Plata_preobrz.docx, (зам D11)'
])

print("ТЕСТ 2: Одна замена")
result2 = smart_aggregate_source_file(test_sources2)
print(f"Результат: '{result2}'")

