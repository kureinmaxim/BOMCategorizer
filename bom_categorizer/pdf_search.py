# -*- coding: utf-8 -*-
"""
Модуль поиска PDF документации для компонентов

Поддерживает:
- Локальный поиск в папках с PDF файлами
- AI-поиск через Anthropic Claude или OpenAI GPT
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json


class LocalPDFSearcher:
    """Класс для локального поиска PDF файлов"""
    
    def __init__(self, base_directory: Optional[str] = None):
        """
        Инициализация поисковика
        
        Args:
            base_directory: Базовая директория для поиска (по умолчанию - папка с БД)
        """
        self.base_directory = base_directory
        
    def search(self, query: str, min_match_length: int = 3) -> List[Dict[str, str]]:
        """
        Поиск PDF файлов по запросу
        
        Args:
            query: Поисковый запрос (название компонента)
            min_match_length: Минимальная длина совпадения подряд
            
        Returns:
            Список найденных файлов с метаданными
        """
        results = []
        
        if not self.base_directory or not os.path.exists(self.base_directory):
            return results
        
        # Нормализуем запрос (убираем пробелы, приводим к верхнему регистру)
        query_normalized = query.strip().upper()
        
        # Ищем в папках, начинающихся с "pdf"
        for root, dirs, files in os.walk(self.base_directory):
            # Фильтруем только папки, начинающиеся с "pdf"
            folder_name = os.path.basename(root).lower()
            if not folder_name.startswith('pdf'):
                # Ограничиваем поиск только папками с pdf в начале
                dirs[:] = [d for d in dirs if d.lower().startswith('pdf')]
                continue
            
            # Ищем PDF файлы
            for file in files:
                if not file.lower().endswith('.pdf'):
                    continue
                
                # Проверяем совпадение в названии файла
                file_normalized = os.path.splitext(file)[0].upper()
                
                # Ищем совпадение подряд min_match_length символов
                if self._has_match(query_normalized, file_normalized, min_match_length):
                    file_path = os.path.join(root, file)
                    results.append({
                        'filename': file,
                        'path': file_path,
                        'folder': os.path.basename(root),
                        'size': self._format_file_size(os.path.getsize(file_path))
                    })
        
        # Сортируем по релевантности (точное совпадение в начале приоритетнее)
        results.sort(key=lambda x: self._calculate_relevance(query_normalized, x['filename']), reverse=True)
        
        return results
    
    def _has_match(self, query: str, filename: str, min_length: int) -> bool:
        """Проверяет наличие совпадения подряд min_length символов"""
        # Убираем все не-алфавитно-цифровые символы для сравнения
        query_clean = re.sub(r'[^A-Z0-9А-ЯЁ]', '', query)
        filename_clean = re.sub(r'[^A-Z0-9А-ЯЁ]', '', filename)
        
        # Ищем любую подстроку из query длиной >= min_length в filename
        for i in range(len(query_clean) - min_length + 1):
            substring = query_clean[i:i + min_length]
            if substring in filename_clean:
                return True
        
        return False
    
    def _calculate_relevance(self, query: str, filename: str) -> float:
        """Вычисляет релевантность результата"""
        query_clean = re.sub(r'[^A-Z0-9А-ЯЁ]', '', query)
        filename_clean = re.sub(r'[^A-Z0-9А-ЯЁ]', '', filename.upper())
        
        # Точное совпадение - максимальный приоритет
        if query_clean in filename_clean:
            # Совпадение в начале файла важнее
            if filename_clean.startswith(query_clean):
                return 100.0
            return 50.0 + (len(query_clean) / len(filename_clean)) * 50
        
        # Частичное совпадение - считаем количество совпадающих символов подряд
        max_match = 0
        for i in range(len(query_clean)):
            for j in range(i + 1, len(query_clean) + 1):
                substring = query_clean[i:j]
                if substring in filename_clean:
                    max_match = max(max_match, len(substring))
        
        return float(max_match)
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Форматирует размер файла в читаемый вид"""
        for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} ТБ"


class AIPDFSearcher:
    """Класс для AI-поиска информации о компонентах"""
    
    def __init__(self, api_provider: str = "anthropic", api_key: Optional[str] = None):
        """
        Инициализация AI поисковика
        
        Args:
            api_provider: Провайдер API ("anthropic" или "openai")
            api_key: API ключ
        """
        self.api_provider = api_provider.lower()
        self.api_key = api_key
        
    def search(self, component_name: str) -> Optional[Dict[str, any]]:
        """
        Поиск информации о компоненте через AI
        
        Args:
            component_name: Название компонента
            
        Returns:
            Словарь с информацией о компоненте или None при ошибке
        """
        if not self.api_key:
            return {
                'error': 'API ключ не установлен',
                'component': component_name
            }
        
        if self.api_provider == "anthropic":
            return self._search_anthropic(component_name)
        elif self.api_provider == "openai":
            return self._search_openai(component_name)
        else:
            return {
                'error': f'Неизвестный провайдер: {self.api_provider}',
                'component': component_name
            }
    
    def _search_anthropic(self, component_name: str) -> Dict[str, any]:
        """Поиск через Anthropic Claude API"""
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=self.api_key)
            
            prompt = f"""Найди информацию об электронном компоненте: {component_name}

Пожалуйста, предоставь следующую информацию в структурированном виде:

1. Полное название и производитель
2. Тип компонента (микросхема, резистор, конденсатор и т.д.)
3. Основные характеристики (напряжение, ток, частота, корпус и т.д.)
4. Краткое описание назначения
5. Типичные примеры использования (2-3 примера)
6. Прямая ссылка на PDF документацию (желательно с официального сайта производителя)

Если компонент не найден или информация недоступна, укажи это явно.

Формат ответа: JSON
{{
    "found": true/false,
    "full_name": "полное название",
    "manufacturer": "производитель",
    "type": "тип компонента",
    "description": "описание",
    "specifications": {{
        "key": "value"
    }},
    "examples": ["пример 1", "пример 2"],
    "datasheet_url": "https://..."
}}"""

            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Парсим ответ
            response_text = message.content[0].text
            
            # Пытаемся извлечь JSON из ответа
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                result = json.loads(json_match.group(0))
                result['component'] = component_name
                result['provider'] = 'Anthropic Claude'
                return result
            else:
                return {
                    'component': component_name,
                    'provider': 'Anthropic Claude',
                    'error': 'Не удалось распарсить ответ',
                    'raw_response': response_text
                }
                
        except Exception as e:
            return {
                'component': component_name,
                'provider': 'Anthropic Claude',
                'error': str(e)
            }
    
    def _search_openai(self, component_name: str) -> Dict[str, any]:
        """Поиск через OpenAI GPT API"""
        try:
            import openai
            
            client = openai.OpenAI(api_key=self.api_key)
            
            prompt = f"""Найди информацию об электронном компоненте: {component_name}

Пожалуйста, предоставь следующую информацию в структурированном JSON виде:

1. Полное название и производитель
2. Тип компонента (микросхема, резистор, конденсатор и т.д.)
3. Основные характеристики (напряжение, ток, частота, корпус и т.д.)
4. Краткое описание назначения
5. Типичные примеры использования (2-3 примера)
6. Прямая ссылка на PDF документацию (желательно с официального сайта производителя)

Формат ответа: JSON
{{
    "found": true/false,
    "full_name": "полное название",
    "manufacturer": "производитель",
    "type": "тип компонента",
    "description": "описание",
    "specifications": {{
        "key": "value"
    }},
    "examples": ["пример 1", "пример 2"],
    "datasheet_url": "https://..."
}}

Отвечай только JSON, без дополнительного текста."""

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Ты - эксперт по электронным компонентам. Отвечай только в формате JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=2048
            )
            
            result = json.loads(response.choices[0].message.content)
            result['component'] = component_name
            result['provider'] = 'OpenAI GPT-4o'
            return result
            
        except Exception as e:
            return {
                'component': component_name,
                'provider': 'OpenAI GPT',
                'error': str(e)
            }


def get_default_pdf_directories() -> List[str]:
    """Возвращает список директорий по умолчанию для поиска PDF"""
    from .component_database import get_database_path
    
    directories = []
    
    # Папка с базой данных
    db_path = get_database_path()
    db_dir = os.path.dirname(db_path)
    directories.append(db_dir)
    
    # Родительская папка базы данных
    parent_dir = os.path.dirname(db_dir)
    directories.append(parent_dir)
    
    return directories

