```python
import json
import time
import requests
import base64
from typing import Dict, List, Optional, Any, List
from PySide6.QtCore import QThread, Signal, QObject

try:
    from ..encryption import SecureMessenger, EncryptionError
except ImportError:
    # Fallback for when running from different context
    try:
        from bom_categorizer.encryption import SecureMessenger, EncryptionError
    except ImportError:
        SecureMessenger = None
        EncryptionError = None


class AIClassifierWorker(QThread):
    """Фоновый поток для AI классификации компонентов"""
    
    # Сигналы
    classification_ready = Signal(str, str, str)  # component_name, category, confidence
    error_occurred = Signal(str)
    progress_update = Signal(str)
    
    def __init__(self, component_name: str, provider: str, api_key: str, model: str = None, 
                 telegram_url: str = None, encryption_key: str = None, use_encryption: bool = True, app_id: str = "bomcategorizer-v5"):
        super().__init__()
        self.component_name = component_name
        self.provider = provider.lower()
        self.api_key = api_key
        self.model = model or self._get_default_model()
        self.telegram_url = telegram_url
        self.encryption_key = encryption_key
        self.use_encryption = use_encryption
        self.app_id = app_id
        
    def _get_default_model(self) -> str:
        """Получить модель по умолчанию для провайдера"""
        defaults = {
            "anthropic": "claude-3-sonnet-20240229",
            "openai": "gpt-4",
            "ollama": "llama2",
            "telegram": "telegram-default"
        }
        return defaults.get(self.provider, "gpt-4")
    
    def run(self):
        """Запуск классификации"""
        try:
            self.progress_update.emit(f"Отправка запроса к {self.provider}...")
            
            if self.provider == "anthropic":
                result = self._classify_anthropic()
            elif self.provider == "openai":
                result = self._classify_openai()
            elif self.provider == "ollama":
                result = self._classify_ollama()
            elif self.provider == "telegram":
                result = self._classify_telegram()
            else:
                raise ValueError(f"Неподдерживаемый провайдер: {self.provider}")
            
            if result:
                category, confidence = result
                self.classification_ready.emit(self.component_name, category, confidence)
            else:
                self.error_occurred.emit("Не удалось получить классификацию")
                
        except Exception as e:
            self.error_occurred.emit(f"Ошибка: {str(e)}")

    def _classify_telegram(self) -> Optional[tuple[str, str]]:
        """Классификация через TelegramHelper API"""
        try:
            import requests
        except ImportError:
            raise ImportError("Установите библиотеку: pip install requests")
            
        if not self.telegram_url:
            raise ValueError("Telegram URL не настроен")
            
        prompt = self._build_classification_prompt()
        
        if self.use_encryption:
            return self._classify_telegram_secure(self.component_name, prompt)
        else:
            return self._classify_telegram_plain(self.component_name, prompt)

    def _classify_telegram_secure(self, component: str, prompt: str) -> Dict:
        """Классификация через Telegram Bot API с шифрованием и маскировкой"""
        if not self.encryption_key:
            return {"error": "Encryption key not configured"}
            
        if not SecureMessenger:
            return {"error": "Encryption module not found"}

        try:
            # Инициализируем шифрование
            messenger = SecureMessenger(self.encryption_key)
            
            # Подготавливаем данные (api_key и app_id ВНУТРИ зашифрованного payload!)
            request_data = {
                "api_key": self.api_key,  # ВАЖНО: передаём api_key внутри шифрования
                "app_id": self.app_id,    # ВАЖНО: передаём app_id внутри шифрования
                "prompt": prompt,         # Исправлено: было "query", должно быть "prompt"
                "provider": "openai",
                "model": "gpt-4"
            }
            
            # 1. Шифруем данные
            encrypted_bytes = messenger.encrypt(request_data)
            
            # 2. Маскируем трафик (Base64 + JSON)
            # Это делает запрос похожим на обычный REST API JSON
            b64_payload = base64.b64encode(encrypted_bytes).decode('utf-8')
            
            # Отправляем запрос на obfuscated endpoint
            # Если URL заканчивается на /ai_query, заменяем на /ai_query/secure
            # Если нет, предполагаем, что пользователь ввел базовый URL
            base_url = self.telegram_url.rstrip('/')
            if base_url.endswith('/ai_query'):
                endpoint = base_url.replace('/ai_query', '/ai_query/secure')
            elif base_url.endswith('/ai_query/encrypted'):
                endpoint = base_url.replace('/ai_query/encrypted', '/ai_query/secure')
            else:
                endpoint = f"{base_url}/ai_query/secure"
                
            # ПРИМЕЧАНИЕ: X-API-KEY и X-APP-ID в заголовках теперь необязательны,
            # так как credentials передаются внутри зашифрованного payload.
            # X-APP-ID в заголовке используется только для выбора ключа шифрования.
            response = requests.post(
                endpoint,
                json={"data": b64_payload},
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "X-APP-ID": self.app_id  # Для выбора ключа шифрования на сервере
                },
                timeout=60
            )
            
            if response.status_code != 200:
                return {"error": f"API Error: {response.status_code} - {response.text}"}
                
            # 3. Разбираем ответ
            try:
                response_json = response.json()
                if "data" not in response_json:
                     return {"error": "Invalid response format: missing 'data' field"}
                     
                # 4. Декодируем Base64
                encrypted_response_bytes = base64.b64decode(response_json["data"])
                
                # 5. Расшифровываем
                decrypted_response = messenger.decrypt(encrypted_response_bytes)
                
                # Если вернулись байты, декодируем в JSON
                if isinstance(decrypted_response, bytes):
                    response_data = json.loads(decrypted_response.decode('utf-8'))
                else:
                    response_data = decrypted_response
                    
                # The Telegram bot returns a text response, which needs to be parsed
                # We'll try to parse it using the existing _parse_classification_response logic
                parsed_classification = self._parse_classification_response(response_data.get("response", ""))
                
                if parsed_classification:
                    category, confidence = parsed_classification
                    return {
                        "category": category,
                        "description": response_data.get("response", ""),
                        "confidence": confidence,
                        "reasoning": "Classified by Telegram Bot AI",
                        "raw_response": response_data.get("response", "")
                    }
                else:
                    # Fallback if parsing fails, return a generic category
                    return {
                        "category": "others", # Default category if parsing fails
                        "description": response_data.get("response", ""),
                        "confidence": "low",
                        "reasoning": "Telegram Bot AI response parsing failed",
                        "raw_response": response_data.get("response", "")
                    }
                
            except Exception as e:
                return {"error": f"Failed to process response: {str(e)}"}
                
        except Exception as e:
            return {"error": f"Encryption/Network error: {str(e)}"}
    def _classify_telegram_plain(self, component: str, prompt: str) -> Dict:
        """Классификация через Telegram Bot API без шифрования (HTTP)"""
        try:
            # Подготавливаем данные
            request_data = {
                "query": prompt,
                "provider": "openai",
                "model": "gpt-4"
            }
            
            # Определяем endpoint (убираем /secure если есть)
            base_url = self.telegram_url.rstrip('/')
            if base_url.endswith('/ai_query/secure'):
                endpoint = base_url.replace('/ai_query/secure', '/ai_query')
            elif base_url.endswith('/ai_query'):
                endpoint = base_url
            else:
                endpoint = f"{base_url}/ai_query"
                
            response = requests.post(
                endpoint,
                json=request_data,
                headers={
                    "Content-Type": "application/json",
                    "X-API-KEY": self.api_key,
                    "X-APP-ID": self.app_id
                },
                timeout=60
            )
            
            if response.status_code != 200:
                return {"error": f"API Error: {response.status_code} - {response.text}"}
                
            response_data = response.json()
            
            # Парсим ответ
            parsed_classification = self._parse_classification_response(response_data.get("response", ""))
            
            if parsed_classification:
                category, confidence = parsed_classification
                return {
                    "category": category,
                    "description": response_data.get("response", ""),
                    "confidence": confidence,
                    "reasoning": "Classified by Telegram Bot AI (Plain)",
                    "raw_response": response_data.get("response", "")
                }
            else:
                return {
                    "category": "others",
                    "description": response_data.get("response", ""),
                    "confidence": "low",
                    "reasoning": "Telegram Bot AI response parsing failed",
                    "raw_response": response_data.get("response", "")
                }
                
        except Exception as e:
            return {"error": f"Network error: {str(e)}"}
    def _classify_anthropic(self) -> Optional[tuple[str, str]]:
        """Классификация через Anthropic Claude API"""
        try:
            import anthropic
        except ImportError:
            raise ImportError("Установите библиотеку: pip install anthropic")
        
        client = anthropic.Anthropic(api_key=self.api_key)
        
        prompt = self._build_classification_prompt()
        
        try:
            message = client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = message.content[0].text
            return self._parse_classification_response(response_text)
            
        except Exception as e:
            raise Exception(f"Ошибка API Anthropic: {str(e)}")
    
    def _classify_openai(self) -> Optional[tuple[str, str]]:
        """Классификация через OpenAI GPT API"""
        try:
            import openai
        except ImportError:
            raise ImportError("Установите библиотеку: pip install openai")
        
        client = openai.OpenAI(api_key=self.api_key)
        
        prompt = self._build_classification_prompt()
        
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Ты эксперт по электронным компонентам. Классифицируй компоненты по категориям."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            response_text = response.choices[0].message.content
            return self._parse_classification_response(response_text)
            
        except Exception as e:
            raise Exception(f"Ошибка API OpenAI: {str(e)}")
    
    def _classify_ollama(self) -> Optional[tuple[str, str]]:
        """Классификация через Ollama (локальный LLM)"""
        try:
            import requests
        except ImportError:
            raise ImportError("Установите библиотеку: pip install requests")
        
        prompt = self._build_classification_prompt()
        
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            response_text = result.get("response", "")
            return self._parse_classification_response(response_text)
            
        except Exception as e:
            raise Exception(f"Ошибка Ollama: {str(e)}")
    
    def _build_classification_prompt(self) -> str:
        """Построить промпт для классификации"""
        categories = {
            "resistors": "Резисторы",
            "capacitors": "Конденсаторы",
            "inductors": "Индуктивности",
            "semiconductors": "Полупроводники (диоды, транзисторы)",
            "ics": "Микросхемы",
            "connectors": "Разъемы",
            "optics": "Оптика (светодиоды, фотодиоды, оптопары)",
            "rf_modules": "СВЧ модули (аттенюаторы, усилители, фильтры)",
            "cables": "Кабели",
            "power_modules": "Модули питания",
            "dev_boards": "Отладочные платы",
            "our_developments": "Наши разработки",
            "others": "Другие компоненты"
        }
        
        categories_list = "\n".join([f"- {key}: {value}" for key, value in categories.items()])
        
        prompt = f"""Классифицируй электронный компонент по названию.

Название компонента: "{self.component_name}"

Доступные категории:
{categories_list}

Задача: Определи наиболее подходящую категорию для этого компонента.

Ответ должен быть в формате JSON:
{{
    "category": "ключ_категории",
    "confidence": "high|medium|low",
    "explanation": "краткое объяснение выбора"
}}

Примеры:
- "Резистор С2-23-0.125-10 кОм" → {{"category": "resistors", "confidence": "high", "explanation": "Явно резистор по названию и номиналу"}}
- "Аттенюатор BW-S2W2+" → {{"category": "rf_modules", "confidence": "high", "explanation": "Аттенюатор - СВЧ компонент"}}
- "Диод 1N4148" → {{"category": "semiconductors", "confidence": "high", "explanation": "Диод - полупроводниковый прибор"}}
- "IC STM32F103" → {{"category": "ics", "confidence": "high", "explanation": "Микроконтроллер - микросхема"}}

Отвечай ТОЛЬКО JSON, без дополнительного текста."""
        
        return prompt
    
    def _parse_classification_response(self, response: str) -> Optional[tuple[str, str]]:
        """Распарсить ответ от LLM"""
        try:
            # Попробуем найти JSON в ответе
            import re
            json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                
                category = data.get("category", "")
                confidence = data.get("confidence", "low")
                
                # Валидация категории
                valid_categories = [
                    "resistors", "capacitors", "inductors", "semiconductors",
                    "ics", "connectors", "optics", "rf_modules", "cables",
                    "power_modules", "dev_boards", "our_developments", "others"
                ]
                
                if category in valid_categories:
                    return (category, confidence)
            
            return None
            
        except Exception as e:
            print(f"Ошибка парсинга ответа: {e}")
            return None


class AIClassifierSettings:
    """Управление настройками AI классификатора"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            # Используем config_qt.json в корне проекта
            # __file__ = bom_categorizer/gui/ai_classifier.py
            # Нужно 3 уровня вверх: gui -> bom_categorizer -> корень проекта
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_path = os.path.join(project_root, "config_qt.json")
        
        self.config_path = config_path
        self.full_config = self._load_full_config()
        self.settings = self.full_config.get("ai_classifier", self._get_default_settings())
    
    def _load_full_config(self) -> Dict[str, Any]:
        """Загружает весь файл конфигурации"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Ошибка полной загрузки конфига: {e}")
        return {}

    def _get_default_settings(self) -> Dict[str, Any]:
        """Возвращает настройки по умолчанию для секции ai_classifier"""
        return {
            "enabled": False,
            "provider": "anthropic",
            "model": "",
            "auto_classify": False,
            "confidence_threshold": "medium",
            "telegram_api_url": "http://localhost:8000",
            "encryption_key": "",
            "use_encryption": True
        }

    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """Сохранить настройки секции ai_classifier в конфиг"""
        try:
            # Обновляем секцию AI в полном конфиге
            self.full_config["ai_classifier"] = settings
            
            # Сохраняем весь конфиг
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.full_config, f, indent=2, ensure_ascii=False)
            
            self.settings = settings
            return True
            
        except Exception as e:
            print(f"Ошибка сохранения настроек AI: {e}")
            return False
    
    def get_provider(self) -> str:
        """Получить выбранного провайдера"""
        return self.settings.get("provider", "anthropic")
    
    def get_api_key(self, provider: str = None) -> str:
        """Получить API ключ из центральной секции api_keys"""
        if provider is None:
            provider = self.get_provider()
        
        api_keys = self.full_config.get("api_keys", {})
        
        if provider == "ollama":
            # Для Ollama ключ - это URL
            return api_keys.get("ollama_url", "")
        
        return api_keys.get(provider, "")
    
    def get_model(self) -> str:
        """Получить название модели"""
        return self.settings.get("model", "")
    
    def is_enabled(self) -> bool:
        """Проверить, включен ли AI классификатор"""
        return self.settings.get("enabled", False)
    
    def is_auto_classify(self) -> bool:
        """Проверить, включена ли автоматическая классификация"""
        return self.settings.get("auto_classify", False)
    
    def get_confidence_threshold(self) -> str:
        """Получить порог уверенности (high, medium, low)"""
        return self.settings.get("confidence_threshold", "medium")

    def get_telegram_url(self) -> str:
        """Получить URL Telegram API"""
        return self.settings.get("telegram_api_url", "http://localhost:8000")

    def get_encryption_key(self) -> str:
        """Получить ключ шифрования"""
        # Сначала ищем в секции api_keys (новое место)
        api_keys = self.full_config.get("api_keys", {})
        key = api_keys.get("telegram_enc_key")
        
        if key:
            return key
            
        # Если нет, ищем в старом месте (ai_classifier section)
        return self.settings.get("encryption_key", "")

    def get_use_encryption(self) -> bool:
        """Использовать ли шифрование"""
        # Сначала ищем в секции api_keys
        api_keys = self.full_config.get("api_keys", {})
        if "telegram_use_encryption" in api_keys:
            return api_keys.get("telegram_use_encryption", True)
            
        return self.settings.get("use_encryption", True)

    def get_app_id(self) -> str:
        """Получить APP_ID для запросов"""
        # Сначала ищем в секции telegram_security (новое место)
        telegram_security = self.full_config.get("telegram_security", {})
        app_id = telegram_security.get("app_id")
        
        if app_id:
            return app_id
        
        # Потом ищем в секции api_keys (альтернативное место)
        api_keys = self.full_config.get("api_keys", {})
        app_id = api_keys.get("app_id")
        
        if app_id:
            return app_id
            
        # Fallback на значение по умолчанию
        return "bomcategorizer-v5"




def classify_component_with_ai(
    component_name: str,
    provider: str,
    api_key: str,
    model: str = None,
    callback = None,
    telegram_url: str = None,
    encryption_key: str = None,
    app_id: str = "bomcategorizer-v5"
) -> Optional[tuple[str, str]]:
    """
    Синхронная функция для классификации компонента через AI
    
    Args:
        component_name: Название компонента
        provider: Провайдер AI (anthropic, openai, ollama, telegram)
        api_key: API ключ
        model: Название модели (опционально)
        callback: Функция обратного вызова для прогресса
        telegram_url: URL Telegram API (для провайдера telegram)
        encryption_key: Ключ шифрования (для провайдера telegram)
    
    Returns:
        Tuple (category, confidence) или None
    """
    worker = AIClassifierWorker(
        component_name, provider, api_key, model, 
        telegram_url=telegram_url, encryption_key=encryption_key, app_id=app_id
    )
    
    result = [None]  # Используем список для изменяемости в замыкании
    
    def on_ready(name, category, confidence):
        result[0] = (category, confidence)
    
    def on_error(error):
        if callback:
            callback(f"Ошибка: {error}")
    
    def on_progress(message):
        if callback:
            callback(message)
    
    worker.classification_ready.connect(on_ready)
    worker.error_occurred.connect(on_error)
    worker.progress_update.connect(on_progress)
    
    # Запускаем синхронно
    worker.run()
    
    return result[0]


if __name__ == "__main__":
    """Тестирование модуля"""
    print("AI Classifier Module - Тестирование")
    print("=" * 50)
    
    # Тест настроек
    settings = AIClassifierSettings()
    print(f"Провайдер: {settings.get_provider()}")
    print(f"Включен: {settings.is_enabled()}")
    print(f"Автоклассификация: {settings.is_auto_classify()}")
    print(f"Telegram URL: {settings.get_telegram_url()}")
    
    print("\nДля реального тестирования необходим API ключ.")
    print("Настройте ключи через GUI: Экспертный режим → AI-подсказки → Настройки")

