import json
import os
import time
from typing import Optional, Dict, Any, List
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
                 telegram_url: str = None, encryption_key: str = None):
        super().__init__()
        self.component_name = component_name
        self.provider = provider.lower()
        self.api_key = api_key
        self.model = model or self._get_default_model()
        self.telegram_url = telegram_url
        self.encryption_key = encryption_key
        
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
        """Классификация через TelegramHelper API (Encrypted)"""
        try:
            import requests
        except ImportError:
            raise ImportError("Установите библиотеку: pip install requests")
            
        if not self.telegram_url:
            raise ValueError("Не указан URL Telegram API")
            
        if not self.encryption_key:
            raise ValueError("Не указан ключ шифрования для Telegram API")
            
        if not SecureMessenger:
            raise ImportError("Модуль шифрования не найден")

        try:
            messenger = SecureMessenger(self.encryption_key)
        except Exception as e:
            raise ValueError(f"Ошибка инициализации шифрования: {e}")

        prompt = self._build_classification_prompt()
        
        # Подготовка данных запроса
        payload = {
            "prompt": prompt,
            "provider": "anthropic", # TelegramHelper использует Anthropic под капотом по умолчанию
            "max_tokens": 500
        }
        
        try:
            # Шифруем данные
            encrypted_data = messenger.encrypt(payload)
            
            # Формируем заголовки
            headers = {
                "X-API-KEY": self.api_key, # Используем API ключ для аутентификации
                "X-APP-ID": "bomcategorizer-v4",
                "X-Timestamp": str(int(time.time())),
                "X-Nonce": os.urandom(8).hex(),
                "Content-Type": "application/octet-stream"
            }
            
            # URL для зашифрованного запроса
            url = f"{self.telegram_url.rstrip('/')}/ai_query/encrypted"
            
            response = requests.post(
                url,
                data=encrypted_data,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            # Расшифровываем ответ
            decrypted_response = messenger.decrypt(response.content)
            
            if isinstance(decrypted_response, dict):
                response_text = decrypted_response.get("response", "")
                return self._parse_classification_response(response_text)
            else:
                raise ValueError("Получен некорректный ответ от сервера")
                
        except Exception as e:
            raise Exception(f"Ошибка Telegram API: {str(e)}")

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
            "encryption_key": ""
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
        return self.settings.get("encryption_key", "")


def classify_component_with_ai(
    component_name: str,
    provider: str,
    api_key: str,
    model: str = None,
    callback = None,
    telegram_url: str = None,
    encryption_key: str = None
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
        telegram_url=telegram_url, encryption_key=encryption_key
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

