#!/usr/bin/env python3
"""
Быстрая проверка статуса сервисов
Запуск: python check_services.py
"""

import requests
import sys

BASE_URL = "http://localhost:8000"
TIMEOUT = 5

def check_api_gateway():
    """Проверка API Gateway"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=TIMEOUT)
        return response.status_code == 200
    except:
        return False

def main():
    print("🔍 ПРОВЕРКА СТАТУСА СЕРВИСОВ")
    print("=" * 40)

    if check_api_gateway():
        print("✅ API Gateway: ЗАПУЩЕН")
        print("\n🎉 Система готова к тестированию!")
        print("Запустите: python comprehensive_test.py")
        sys.exit(0)
    else:
        print("❌ API Gateway: НЕДОСТУПЕН")
        print("\n🔧 ИНСТРУКЦИЯ ПО ЗАПУСКУ:")
        print("1. Убедитесь, что Docker Desktop запущен")
        print("2. Откройте терминал в папке проекта")
        print("3. Выполните команду:")
        print("   docker-compose up --build -d")
        print("4. Подождите 2-3 минуты")
        print("5. Запустите эту проверку снова")
        print("\n💡 Если проблема persists, проверьте логи:")
        print("   docker-compose logs api-gateway")
        sys.exit(1)

if __name__ == "__main__":
    main()