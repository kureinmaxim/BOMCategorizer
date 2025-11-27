import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bom_categorizer.encryption import SecureMessenger
from bom_categorizer.gui.ai_classifier import classify_component_with_ai

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_integration():
    # Configuration (Match with TelegramHelper test env)
    TELEGRAM_URL = "http://localhost:8000"
    API_KEY = "test_secret_key_32_bytes_long_12345" 
    ENCRYPTION_KEY = "test_secret_key_32_bytes_long_12345"
    
    print(f"Testing integration with {TELEGRAM_URL}...")
    
    def callback(msg):
        print(f"Progress: {msg}")
        
    try:
        result = classify_component_with_ai(
            component_name="Resistor 10k 0603",
            provider="telegram",
            api_key=API_KEY,
            telegram_url=TELEGRAM_URL,
            encryption_key=ENCRYPTION_KEY,
            callback=callback
        )
        
        if result:
            category, confidence = result
            print(f"SUCCESS! Category: {category}, Confidence: {confidence}")
        else:
            print("FAILED: No result returned")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_integration()
