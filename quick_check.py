#!/usr/bin/env python3
import requests
import sys

try:
    response = requests.get("http://localhost:8000/", timeout=3)
    if response.status_code == 200:
        print("✅ API Gateway доступен")
        sys.exit(0)
    else:
        print(f"❌ API Gateway вернул {response.status_code}")
        sys.exit(1)
except requests.exceptions.RequestException as e:
    print(f"❌ Ошибка подключения: {e}")
    sys.exit(1)