# -*- coding: utf-8 -*-
"""
Модуль шифрования для безопасной передачи данных

Использует AES-256-GCM для шифрования и HMAC для аутентификации.
"""

import os
import json
import hashlib
import hmac
from typing import Union, Dict, Any


class EncryptionError(Exception):
    """Ошибка шифрования/расшифровки"""
    pass


class SecureMessenger:
    """
    Класс для безопасного шифрования и расшифровки данных.
    
    Использует AES-256-GCM (через cryptography) или Fernet как fallback.
    """
    
    def __init__(self, key: str):
        """
        Инициализация с ключом шифрования.
        
        Args:
            key: Ключ в hex формате (64 символа для 256 бит)
        """
        if not key:
            raise EncryptionError("Encryption key is required")
        
        # Преобразуем hex ключ в bytes
        try:
            self.key = bytes.fromhex(key)
        except ValueError:
            # Если не hex, используем как строку и хешируем
            self.key = hashlib.sha256(key.encode()).digest()
        
        # Проверяем доступность cryptography
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            self._aesgcm = AESGCM(self.key[:32])  # AES-256 требует 32 байта
            self._use_aesgcm = True
        except ImportError:
            # Fallback на Fernet
            try:
                from cryptography.fernet import Fernet
                import base64
                # Создаем Fernet-совместимый ключ из нашего ключа
                fernet_key = base64.urlsafe_b64encode(self.key[:32])
                self._fernet = Fernet(fernet_key)
                self._use_aesgcm = False
            except ImportError:
                raise EncryptionError("cryptography library is required. Install with: pip install cryptography")
    
    def encrypt(self, data: Union[bytes, dict, str]) -> bytes:
        """
        Шифрует данные.
        
        Args:
            data: Данные для шифрования (bytes, dict или str)
            
        Returns:
            Зашифрованные данные в формате: nonce (12 bytes) + ciphertext
        """
        # Преобразуем данные в bytes
        if isinstance(data, dict):
            plaintext = json.dumps(data, ensure_ascii=False).encode('utf-8')
        elif isinstance(data, str):
            plaintext = data.encode('utf-8')
        else:
            plaintext = data
        
        if self._use_aesgcm:
            # AES-GCM шифрование
            nonce = os.urandom(12)  # 96 бит для GCM
            ciphertext = self._aesgcm.encrypt(nonce, plaintext, None)
            return nonce + ciphertext
        else:
            # Fernet шифрование
            return self._fernet.encrypt(plaintext)
    
    def decrypt(self, data: bytes) -> bytes:
        """
        Расшифровывает данные.
        
        Args:
            data: Зашифрованные данные
            
        Returns:
            Расшифрованные данные как bytes
        """
        try:
            if self._use_aesgcm:
                # AES-GCM расшифровка
                nonce = data[:12]
                ciphertext = data[12:]
                return self._aesgcm.decrypt(nonce, ciphertext, None)
            else:
                # Fernet расшифровка
                return self._fernet.decrypt(data)
        except Exception as e:
            raise EncryptionError(f"Decryption failed: {e}")
    
    def encrypt_json(self, data: dict) -> str:
        """
        Шифрует данные и возвращает base64 строку.
        
        Args:
            data: Словарь для шифрования
            
        Returns:
            Base64-encoded зашифрованные данные
        """
        import base64
        encrypted = self.encrypt(data)
        return base64.b64encode(encrypted).decode('utf-8')
    
    def decrypt_json(self, data: str) -> dict:
        """
        Расшифровывает base64 строку и возвращает словарь.
        
        Args:
            data: Base64-encoded зашифрованные данные
            
        Returns:
            Расшифрованный словарь
        """
        import base64
        encrypted = base64.b64decode(data)
        decrypted = self.decrypt(encrypted)
        return json.loads(decrypted.decode('utf-8'))
