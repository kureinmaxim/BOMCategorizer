import sys
import os
import json
import urllib.request
import urllib.error

# Add current directory to path to import tools
sys.path.append(os.getcwd())

try:
    from tools.sync_telegram_api import load_config, get_config_paths
except ImportError:
    # Fallback if running from wrong dir
    sys.path.append(os.path.join(os.getcwd(), 'tools'))
    from sync_telegram_api import load_config, get_config_paths

def make_request(url, data, headers, timeout=5):
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status, response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except Exception as e:
        return 0, str(e)

def test():
    print("Loading config...")
    paths = get_config_paths()
    # Try project config first, then installed
    config_path = paths['project']
    if not config_path.exists():
        config_path = paths['installed']
    
    if not config_path.exists():
        print(f"Config file not found at {paths['project']} or {paths['installed']}")
        return

    config = load_config(config_path)
    api_keys = config.get('api_keys', {})
    url = api_keys.get('telegram_url')
    key = api_keys.get('telegram_key')
    
    if not url:
        print("URL not found in config")
        return
    if not key:
        print("API Key not found in config")
        return

    print(f"Target URL: {url}")
    # Mask key for output
    masked_key = key[:4] + "..." + key[-4:] if len(key) > 8 else "***"
    print(f"API Key: {masked_key}")
    
    payload = {
        "prompt": "Test connection",
        "provider": "anthropic",
        "max_tokens": 10
    }

    # Test 1: No X-APP-ID (Legacy/Sync tool mode)
    print("\n--- Test 1: No X-APP-ID ---")
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": key
    }
    print("Sending request...")
    status, response = make_request(url, payload, headers)
    print(f"Status: {status}")
    print(f"Response: {response[:100]}")

    # Test 2: X-APP-ID = bomcategorizer-v5 (Current GUI)
    print("\n--- Test 2: X-APP-ID = bomcategorizer-v5 ---")
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": key,
        "X-APP-ID": "bomcategorizer-v5"
    }
    print("Sending request...")
    status, response = make_request(url, payload, headers)
    print(f"Status: {status}")
    print(f"Response: {response[:100]}")

    # Test 3: X-APP-ID = bomcategorizer-v4 (Old GUI / Server Whitelist)
    print("\n--- Test 3: X-APP-ID = bomcategorizer-v4 ---")
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": key,
        "X-APP-ID": "bomcategorizer-v4"
    }
    print("Sending request...")
    status, response = make_request(url, payload, headers)
    print(f"Status: {status}")
    print(f"Response: {response[:100]}")

if __name__ == "__main__":
    test()
