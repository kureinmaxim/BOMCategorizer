# -*- coding: utf-8 -*-
"""
Модуль поиска PDF документации для компонентов

Поддерживает:
- Локальный поиск в папках с PDF файлами
- AI-поиск через Anthropic Claude или OpenAI GPT
- Безопасное взаимодействие с TelegramHelper API
"""

import os
import re
import hmac
import hashlib
import time
import uuid
import base64
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json

# Импорт SecureMessenger для шифрования
try:
    from ..encryption import SecureMessenger
    ENCRYPTION_AVAILABLE = True
except ImportError:
    try:
        from bom_categorizer.encryption import SecureMessenger
        ENCRYPTION_AVAILABLE = True
    except ImportError:
        SecureMessenger = None
        ENCRYPTION_AVAILABLE = False


def create_signed_headers(
    payload: dict,
    api_key: str,
    hmac_secret: Optional[str] = None,
    app_id: str = "bomcategorizer-v4"
) -> dict:
    """
    Создание заголовков с HMAC подписью для безопасного запроса к TelegramHelper API
    
    Args:
        payload: Тело запроса (будет подписано)
        api_key: API ключ для аутентификации
        hmac_secret: Секрет для HMAC подписи (если не указан, используется api_key)
        app_id: Идентификатор приложения
        
    Returns:
        Словарь заголовков для HTTP запроса
    """
    # Используем api_key как hmac_secret если секрет не указан
    secret = hmac_secret or api_key
    
    # Генерируем timestamp (Unix time)
    timestamp = str(int(time.time()))
    
    # Генерируем уникальный nonce
    nonce = str(uuid.uuid4())
    
    # Формируем строку для подписи (timestamp:nonce:json_payload)
    payload_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    sign_string = f"{timestamp}:{nonce}:{payload_json}"
    
    # Вычисляем HMAC-SHA256 подпись
    signature = hmac.new(
        secret.encode('utf-8'),
        sign_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return {
        "X-API-KEY": api_key,
        "X-APP-ID": app_id,
        "X-Timestamp": timestamp,
        "X-Nonce": nonce,
        "X-Signature": signature,
        "Content-Type": "application/json"
    }


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
        
        # Проверяем, начинается ли сама base_directory с pdf*
        base_name = os.path.basename(self.base_directory).lower()
        is_pdf_folder = base_name.startswith('pdf')
        
        # Ищем в папках, начинающихся с "pdf"
        for root, dirs, files in os.walk(self.base_directory):
            folder_name = os.path.basename(root).lower()
            
            # Если мы уже внутри папки pdf*, то ищем везде рекурсивно
            if is_pdf_folder or root == self.base_directory or folder_name.startswith('pdf'):
                # Продолжаем поиск во всех подпапках
                pass
            else:
                # Если не в папке pdf*, ограничиваем поиск только подпапками с префиксом pdf*
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
    
    def __init__(self, api_provider: str = "anthropic", api_key: Optional[str] = None, 
                 api_url: Optional[str] = None, use_encryption: bool = False, 
                 encryption_key: Optional[str] = None):
        """
        Инициализация AI поисковика
        
        Args:
            api_provider: Провайдер API ("anthropic", "openai" или "telegram_bot")
            api_key: API ключ
            api_url: URL API (для Telegram Bot)
            use_encryption: Использовать ли шифрование для Telegram Bot
            encryption_key: Ключ шифрования (hex string)
        """
        self.api_provider = api_provider.lower()
        self.api_key = api_key
        self.api_url = api_url
        self.use_encryption = use_encryption
        self.encryption_key = encryption_key
        
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
        elif self.api_provider == "telegram_bot":
            return self._search_telegram_bot(component_name)
        else:
            return {
                'error': f'Неизвестный провайдер: {self.api_provider}',
                'component': component_name
            }
    
    def search_with_prompt(self, component_name: str, custom_prompt: str) -> Optional[Dict[str, any]]:
        """
        Поиск информации о компоненте через AI с кастомным промптом
        
        Args:
            component_name: Название компонента
            custom_prompt: Пользовательский промпт
            
        Returns:
            Словарь с информацией о компоненте или None при ошибке
        """
        if not self.api_key:
            return {
                'error': 'API ключ не установлен',
                'component': component_name
            }
        
        if self.api_provider == "anthropic":
            return self._search_with_custom_prompt_anthropic(component_name, custom_prompt)
        elif self.api_provider == "openai":
            return self._search_with_custom_prompt_openai(component_name, custom_prompt)
        elif self.api_provider == "telegram_bot":
            return self._search_with_custom_prompt_telegram(component_name, custom_prompt)
        else:
            return {
                'error': f'Неизвестный провайдер: {self.api_provider}',
                'component': component_name
            }
    
    def _search_with_custom_prompt_anthropic(self, component_name: str, custom_prompt: str) -> Dict[str, any]:
        """Поиск через Anthropic Claude API с кастомным промптом"""
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=self.api_key)

            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": custom_prompt}
                ]
            )
            
            response_text = message.content[0].text
            
            # Пытаемся извлечь JSON из ответа (если есть)
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                try:
                    result = json.loads(json_match.group(0))
                    result['component'] = component_name
                    result['provider'] = 'Anthropic Claude'
                    result['raw_response'] = response_text
                    return result
                except json.JSONDecodeError:
                    pass
            
            # Если JSON не найден, возвращаем текстовый ответ
            return {
                'found': True,
                'component': component_name,
                'provider': 'Anthropic Claude',
                'description': response_text,
                'raw_response': response_text
            }
                
        except Exception as e:
            return {
                'component': component_name,
                'provider': 'Anthropic Claude',
                'error': str(e)
            }
    
    def _search_with_custom_prompt_openai(self, component_name: str, custom_prompt: str) -> Dict[str, any]:
        """Поиск через OpenAI GPT API с кастомным промптом"""
        try:
            import openai
            
            client = openai.OpenAI(api_key=self.api_key)

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Ты эксперт по электронным компонентам и источникам питания."},
                    {"role": "user", "content": custom_prompt}
                ],
                max_tokens=4096
            )
            
            response_text = response.choices[0].message.content
            
            # Пытаемся извлечь JSON из ответа (если есть)
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                try:
                    result = json.loads(json_match.group(0))
                    result['component'] = component_name
                    result['provider'] = 'OpenAI GPT-4o'
                    result['raw_response'] = response_text
                    return result
                except json.JSONDecodeError:
                    pass
            
            # Если JSON не найден, возвращаем текстовый ответ
            return {
                'found': True,
                'component': component_name,
                'provider': 'OpenAI GPT-4o',
                'description': response_text,
                'raw_response': response_text
            }
            
        except Exception as e:
            return {
                'component': component_name,
                'provider': 'OpenAI GPT',
                'error': str(e)
            }
    
    def _search_with_custom_prompt_telegram(self, component_name: str, custom_prompt: str) -> Dict[str, any]:
        """Поиск через Telegram Bot API с кастомным промптом, подписью и опциональным шифрованием"""
        try:
            import requests
            
            base_url = self.api_url or "http://localhost:8000/ai_query"
            
            payload = {
                "prompt": custom_prompt,
                "provider": "anthropic",
                "max_tokens": 4096
            }
            
            # Проверяем, нужно ли шифрование
            if self.use_encryption and self.encryption_key and ENCRYPTION_AVAILABLE:
                # Шифруем запрос
                messenger = SecureMessenger(self.encryption_key)
                request_data = json.dumps(payload).encode('utf-8')
                encrypted_bytes = messenger.encrypt(request_data)
                b64_payload = base64.b64encode(encrypted_bytes).decode('utf-8')
                
                # Определяем endpoint для шифрованных запросов
                url = base_url.rstrip('/')
                if url.endswith('/ai_query'):
                    url = url.replace('/ai_query', '/ai_query/secure')
                elif not url.endswith('/ai_query/secure'):
                    url = f"{url}/ai_query/secure"
                
                headers = {
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                response = requests.post(url, json={"data": b64_payload}, headers=headers, timeout=120)
            else:
                # Обычный запрос без шифрования
                url = base_url
                if self.api_key:
                    headers = create_signed_headers(
                        payload=payload,
                        api_key=self.api_key,
                        hmac_secret=self.api_key,
                        app_id="bomcategorizer-v4"
                    )
                else:
                    headers = {"Content-Type": "application/json"}
                
                response = requests.post(url, json=payload, headers=headers, timeout=120)
            
            if response.status_code != 200:
                return {
                    'component': component_name,
                    'provider': 'Telegram Bot',
                    'error': f"Ошибка сервера: {response.status_code} - {response.text}"
                }
            
            # Обработка ответа
            response_json = response.json()
            
            # Если шифрование включено, расшифровываем ответ
            if self.use_encryption and self.encryption_key and ENCRYPTION_AVAILABLE and "data" in response_json:
                try:
                    messenger = SecureMessenger(self.encryption_key)
                    encrypted_response = base64.b64decode(response_json["data"])
                    decrypted_response = messenger.decrypt(encrypted_response)
                    if isinstance(decrypted_response, bytes):
                        data = json.loads(decrypted_response.decode('utf-8'))
                    else:
                        data = decrypted_response
                except Exception as decrypt_err:
                    return {
                        'component': component_name,
                        'provider': 'Telegram Bot',
                        'error': f"Ошибка расшифровки ответа: {decrypt_err}"
                    }
            else:
                data = response_json
            
            response_text = data.get("response", "")
            model_used = data.get("model", "unknown")
            api_provider = data.get("provider", "anthropic")
            
            # Формируем строку провайдера с моделью
            encryption_tag = " 🔒" if self.use_encryption else ""
            provider_str = f"Telegram Bot ({api_provider}: {model_used}){encryption_tag}"
            
            # Пытаемся извлечь JSON из ответа
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                try:
                    result = json.loads(json_match.group(0))
                    result['component'] = component_name
                    result['provider'] = provider_str
                    result['model'] = model_used
                    result['raw_response'] = response_text
                    return result
                except json.JSONDecodeError:
                    pass
            
            # Если JSON не найден, возвращаем текстовый ответ
            return {
                'found': True,
                'component': component_name,
                'provider': provider_str,
                'model': model_used,
                'description': response_text,
                'raw_response': response_text
            }
                
        except Exception as e:
            return {
                'component': component_name,
                'provider': 'Telegram Bot',
                'error': str(e)
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

    def _search_telegram_bot(self, component_name: str) -> Dict[str, any]:
        """Поиск через Telegram Bot API с подписью запроса и опциональным шифрованием"""
        try:
            import requests
            
            base_url = self.api_url or "http://localhost:8000/ai_query"
            
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

            payload = {
                "prompt": prompt,
                "provider": "anthropic",
                "max_tokens": 2048
            }
            
            # Проверяем, нужно ли шифрование
            if self.use_encryption and self.encryption_key and ENCRYPTION_AVAILABLE:
                # Шифруем запрос
                messenger = SecureMessenger(self.encryption_key)
                request_data = json.dumps(payload).encode('utf-8')
                encrypted_bytes = messenger.encrypt(request_data)
                b64_payload = base64.b64encode(encrypted_bytes).decode('utf-8')
                
                # Определяем endpoint для шифрованных запросов
                url = base_url.rstrip('/')
                if url.endswith('/ai_query'):
                    url = url.replace('/ai_query', '/ai_query/secure')
                elif not url.endswith('/ai_query/secure'):
                    url = f"{url}/ai_query/secure"
                
                headers = {
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                response = requests.post(url, json={"data": b64_payload}, headers=headers, timeout=60)
            else:
                # Обычный запрос без шифрования
                url = base_url
                if self.api_key:
                    headers = create_signed_headers(
                        payload=payload,
                        api_key=self.api_key,
                        hmac_secret=self.api_key,
                        app_id="bomcategorizer-v4"
                    )
                else:
                    headers = {"Content-Type": "application/json"}
                
                response = requests.post(url, json=payload, headers=headers, timeout=60)
            
            if response.status_code != 200:
                return {
                    'component': component_name,
                    'provider': 'Telegram Bot',
                    'error': f"Ошибка сервера: {response.status_code} - {response.text}"
                }
            
            # Обработка ответа
            response_json = response.json()
            
            # Если шифрование включено, расшифровываем ответ
            if self.use_encryption and self.encryption_key and ENCRYPTION_AVAILABLE and "data" in response_json:
                try:
                    messenger = SecureMessenger(self.encryption_key)
                    encrypted_response = base64.b64decode(response_json["data"])
                    decrypted_response = messenger.decrypt(encrypted_response)
                    if isinstance(decrypted_response, bytes):
                        data = json.loads(decrypted_response.decode('utf-8'))
                    else:
                        data = decrypted_response
                except Exception as decrypt_err:
                    return {
                        'component': component_name,
                        'provider': 'Telegram Bot',
                        'error': f"Ошибка расшифровки ответа: {decrypt_err}"
                    }
            else:
                data = response_json
            
            response_text = data.get("response", "")
            model_used = data.get("model", "unknown")
            api_provider = data.get("provider", "anthropic")
            
            # Формируем строку провайдера с моделью
            encryption_tag = " 🔒" if self.use_encryption else ""
            provider_str = f"Telegram Bot ({api_provider}: {model_used}){encryption_tag}"
            
            # Пытаемся извлечь JSON из ответа
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                result = json.loads(json_match.group(0))
                result['component'] = component_name
                result['provider'] = provider_str
                result['model'] = model_used
                return result
            else:
                return {
                    'component': component_name,
                    'provider': provider_str,
                    'model': model_used,
                    'error': 'Не удалось распарсить ответ',
                    'raw_response': response_text
                }
                
        except Exception as e:
            return {
                'component': component_name,
                'provider': 'Telegram Bot',
                'error': str(e)
            }


def get_default_pdf_directories(config: Optional[Dict] = None) -> List[str]:
    """
    Возвращает список директорий по умолчанию для поиска PDF
    
    Ищет в:
    1. Пользовательские папки из config.json (если указаны)
    2. Папка базы данных + все подпапки с префиксом pdf* (любой регистр)
    3. macOS: /Users/olgazaharova/Project + все подпапки с префиксом pdf*
    4. Windows: C:\\Project + все подпапки с префиксом pdf*
    
    Args:
        config: Словарь конфигурации (опционально)
    """
    from ..component_database import get_database_path
    import sys
    
    directories = []
    
    # 1. Пользовательские папки из конфига
    if config:
        custom_dirs = config.get("pdf_search", {}).get("custom_directories", [])
        for custom_dir in custom_dirs:
            if custom_dir and os.path.exists(custom_dir):
                directories.append(custom_dir)
    
    # 2. Папка с базой данных и её подпапки с префиксом pdf*
    db_path = get_database_path()
    db_dir = os.path.dirname(db_path)
    
    # Добавляем саму папку БД
    if os.path.exists(db_dir):
        directories.append(db_dir)
        
        # Ищем подпапки с префиксом pdf* (любой регистр)
        for item in os.listdir(db_dir):
            item_path = os.path.join(db_dir, item)
            if os.path.isdir(item_path) and item.lower().startswith('pdf'):
                directories.append(item_path)
    
    # 3. Дополнительные проектные папки
    if sys.platform == "darwin":  # macOS
        project_dir = "/Users/olgazaharova/Project"
        if os.path.exists(project_dir):
            # Ищем подпапки с префиксом pdf* (любой регистр)
            for item in os.listdir(project_dir):
                item_path = os.path.join(project_dir, item)
                if os.path.isdir(item_path) and item.lower().startswith('pdf'):
                    directories.append(item_path)
    
    elif sys.platform == "win32":  # Windows
        project_dir = "C:\\Project"
        if os.path.exists(project_dir):
            # Ищем подпапки с префиксом pdf* (любой регистр)
            for item in os.listdir(project_dir):
                item_path = os.path.join(project_dir, item)
                if os.path.isdir(item_path) and item.lower().startswith('pdf'):
                    directories.append(item_path)
    
    # Возвращаем уникальные директории
    return list(dict.fromkeys(directories))  # Убираем дубликаты, сохраняя порядок

