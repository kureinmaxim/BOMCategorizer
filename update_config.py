import json
import os

config_path = 'config_qt.json'

if os.path.exists(config_path):
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'api_keys' not in data:
            data['api_keys'] = {}
            
        if 'telegram_enc_key' not in data['api_keys']:
            print("Adding telegram_enc_key to config...")
            # Use the key we know from previous steps if possible, or empty string
            # The user mentioned the key earlier: 13ab4a4f0c5d57ecf93727ad684f1ac46f35971a65511bc962740b8eb8bb79a2
            data['api_keys']['telegram_enc_key'] = "13ab4a4f0c5d57ecf93727ad684f1ac46f35971a65511bc962740b8eb8bb79a2"
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print("Done!")
        else:
            print("Key already exists.")
            
    except Exception as e:
        print(f"Error: {e}")
else:
    print("Config file not found.")
