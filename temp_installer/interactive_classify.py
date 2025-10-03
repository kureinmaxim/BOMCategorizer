#!/usr/bin/env python3
"""
Интерактивный классификатор BOM файлов
Запуск: python interactive_classify.py
"""

import os
import sys
import argparse
from split_bom import main as cli_main

def main():
    print("=== Интерактивный классификатор BOM файлов ===")
    print("Этот скрипт позволяет интерактивно классифицировать компоненты")
    print("Для выхода нажмите Ctrl+C\n")
    
    # Получаем аргументы командной строки
    parser = argparse.ArgumentParser(description="Интерактивная классификация BOM файлов")
    parser.add_argument("--input", required=True, help="Путь к входному файлу")
    parser.add_argument("--output", default="categorized.xlsx", help="Путь к выходному файлу")
    parser.add_argument("--sheets", help="Номера листов (например: 3,4)")
    
    args = parser.parse_args()
    
    # Формируем аргументы для split_bom
    cli_args = ["--inputs", args.input, "--xlsx", args.output, "--interactive", "--combine"]
    
    if args.sheets:
        cli_args.extend(["--sheets", args.sheets])
    
    print(f"Входной файл: {args.input}")
    print(f"Выходной файл: {args.output}")
    if args.sheets:
        print(f"Листы: {args.sheets}")
    print("\nЗапуск интерактивной классификации...\n")
    
    # Заменяем sys.argv для передачи в cli_main
    old_argv = sys.argv
    try:
        sys.argv = ["split_bom.py"] + cli_args
        cli_main()
    finally:
        sys.argv = old_argv

if __name__ == "__main__":
    main()
