import os
import struct
import json
import logging
from typing import Union, Tuple, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

logger = logging.getLogger(__name__)

class EncryptionError(Exception):
    """Base class for encryption errors"""
    pass

class SecureMessenger:
    """
    Handles application-level encryption using AES-256-GCM.
    
    Protocol Format:
    [Version(1B)][KeyID(4B)][Nonce(12B)][Ciphertext(N)][Tag(16B)]
    """
    
    PROTOCOL_VERSION = 1
    NONCE_SIZE = 12
    TAG_SIZE = 16
    KEY_SIZE = 32
    SALT = b'TelegramHelper_v1_Salt'
    INFO = b'AES-256-GCM-Key'
    
    def __init__(self, master_secret: str, key_id: int = 1):
        """
        Initialize SecureMessenger.
        
        Args:
            master_secret: The master secret key (hex string or bytes)
            key_id: Identifier for the key (for rotation support)
        """
        self.key_id = key_id
        
        if isinstance(master_secret, str):
            try:
                # Try to decode if it looks like hex
                if len(master_secret) == 64:
                    self._master_secret = bytes.fromhex(master_secret)
                else:
                    self._master_secret = master_secret.encode()
            except ValueError:
                self._master_secret = master_secret.encode()
        else:
            self._master_secret = master_secret
            
        self._derived_key = self._derive_key(self._master_secret)
        self._aesgcm = AESGCM(self._derived_key)
        
    def _derive_key(self, master_secret: bytes) -> bytes:
        """Derive a 32-byte encryption key using HKDF."""
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=self.KEY_SIZE,
            salt=self.SALT,
            info=self.INFO,
        )
        return hkdf.derive(master_secret)

    def encrypt(self, data: Union[dict, str, bytes]) -> bytes:
        """
        Encrypt data into a binary packet.
        
        Args:
            data: Data to encrypt (dict will be JSON serialized)
            
        Returns:
            bytes: The encrypted packet
        """
        if isinstance(data, dict):
            payload = json.dumps(data).encode('utf-8')
        elif isinstance(data, str):
            payload = data.encode('utf-8')
        else:
            payload = data
            
        nonce = os.urandom(self.NONCE_SIZE)
        
        # AESGCM.encrypt returns ciphertext + tag
        encrypted_data = self._aesgcm.encrypt(nonce, payload, None)
        
        version_bytes = struct.pack('B', self.PROTOCOL_VERSION)
        key_id_bytes = struct.pack('>I', self.key_id)
        
        # Packet structure: Version + KeyID + Nonce + EncryptedData(Ciphertext+Tag)
        packet = version_bytes + key_id_bytes + nonce + encrypted_data
        return packet

    def decrypt(self, packet: bytes) -> Union[dict, bytes]:
        """
        Decrypt a binary packet.
        
        Args:
            packet: The encrypted binary packet
            
        Returns:
            Union[dict, bytes]: Decrypted data (parsed as JSON if possible)
            
        Raises:
            EncryptionError: If decryption fails or protocol is invalid
        """
        if len(packet) < (1 + 4 + self.NONCE_SIZE + self.TAG_SIZE):
            raise EncryptionError("Packet too short")
            
        offset = 0
        version = packet[offset]
        offset += 1
        
        if version != self.PROTOCOL_VERSION:
            raise EncryptionError(f"Unsupported protocol version: {version}")
            
        key_id = struct.unpack('>I', packet[offset:offset+4])[0]
        offset += 4
        
        if key_id != self.key_id:
            # In a real system, we might look up the key by ID here
            logger.warning(f"Received KeyID {key_id}, expected {self.key_id}")
            
        nonce = packet[offset:offset+self.NONCE_SIZE]
        offset += self.NONCE_SIZE
        
        encrypted_data = packet[offset:]
        
        try:
            plaintext = self._aesgcm.decrypt(nonce, encrypted_data, None)
        except Exception as e:
            raise EncryptionError(f"Decryption failed: {e}")
            
        try:
            return json.loads(plaintext.decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return plaintext
