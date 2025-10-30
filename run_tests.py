"""
Скрипт для запуска всех тестов проекта

Использование:
    python run_tests.py                    # Запустить все тесты
    python run_tests.py -v                 # Verbose режим
    python run_tests.py -k test_classifiers  # Запустить только определенные тесты
    python run_tests.py --quick            # Только быстрые unit-тесты
    python run_tests.py --integration      # Только интеграционные тесты
"""

import sys
import subprocess
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description='Запуск тестов BOM Categorizer')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose режим')
    parser.add_argument('-k', '--keyword', type=str,
                       help='Запустить только тесты с определенным ключевым словом')
    parser.add_argument('--quick', action='store_true',
                       help='Только быстрые unit-тесты')
    parser.add_argument('--integration', action='store_true',
                       help='Только интеграционные тесты')
    parser.add_argument('--html', action='store_true',
                       help='Создать HTML отчет')
    parser.add_argument('--coverage', action='store_true',
                       help='Запустить с покрытием кода')
    
    args = parser.parse_args()
    
    # Базовая команда pytest
    cmd = ['pytest']
    
    # Добавляем папку с тестами
    if args.quick:
        # Только unit-тесты (исключаем интеграционные)
        cmd.extend([
            'tests/test_classifiers.py',
            'tests/test_database.py',
            'tests/test_formatters.py'
        ])
        print("🚀 Запуск быстрых unit-тестов...")
    elif args.integration:
        # Только интеграционные
        cmd.append('tests/test_integration.py')
        print("🚀 Запуск интеграционных тестов...")
    else:
        # Все тесты
        cmd.append('tests/')
        print("🚀 Запуск всех тестов...")
    
    # Verbose режим
    if args.verbose:
        cmd.append('-v')
    
    # Фильтр по ключевому слову
    if args.keyword:
        cmd.extend(['-k', args.keyword])
        print(f"   Фильтр: {args.keyword}")
    
    # HTML отчет
    if args.html:
        cmd.extend(['--html=test_report.html', '--self-contained-html'])
        print("   HTML отчет: test_report.html")
    
    # Покрытие кода
    if args.coverage:
        cmd.extend([
            '--cov=bom_categorizer',
            '--cov-report=html',
            '--cov-report=term'
        ])
        print("   Отчет покрытия: htmlcov/index.html")
    
    # Добавляем вывод в консоль для интеграционных тестов
    if args.integration or not (args.quick or args.keyword):
        cmd.append('-s')
    
    # Запускаем
    print(f"\nКоманда: {' '.join(cmd)}\n")
    print("=" * 80)
    
    try:
        result = subprocess.run(cmd, check=False)
        
        print("\n" + "=" * 80)
        if result.returncode == 0:
            print("✅ Все тесты пройдены успешно!")
        else:
            print("❌ Некоторые тесты не прошли")
            print(f"   Код возврата: {result.returncode}")
        
        sys.exit(result.returncode)
        
    except FileNotFoundError:
        print("\n❌ Ошибка: pytest не установлен")
        print("\nУстановите pytest:")
        print("   pip install pytest pytest-html pytest-cov")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Тестирование прервано пользователем")
        sys.exit(130)


if __name__ == '__main__':
    main()
