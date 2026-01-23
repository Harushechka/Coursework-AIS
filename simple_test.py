#!/usr/bin/env python3
"""
Простой тест для проверки работы API Gateway и основных сервисов
Запуск: python simple_test.py
"""

import requests
import time
import sys

BASE_URL = "http://localhost:8000"
TIMEOUT = 10

def test_connection():
    """Проверка базового подключения"""
    print("🔍 Проверка подключения к API Gateway...")

    try:
        response = requests.get(f"{BASE_URL}/", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Gateway доступен. Версия: {data.get('version', 'неизвестна')}")
            return True
        else:
            print(f"❌ API Gateway вернул статус {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        if "Connection refused" in str(e) or "Connection aborted" in str(e):
            print("❌ Не удается подключиться к API Gateway")
            print("💡 Убедитесь, что сервисы запущены: docker-compose up --build -d")
        else:
            print(f"❌ Ошибка подключения: {e}")
        return False
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def test_services():
    """Проверка доступности сервисов"""
    print("\n🔍 Проверка доступности сервисов...")

    try:
        response = requests.get(f"{BASE_URL}/services", timeout=TIMEOUT)
        if response.status_code == 200:
            services = response.json()
            total = len(services.get("services", {}))
            healthy = sum(1 for s in services.get("services", {}).values() if s.get("status") == "healthy")

            print(f"📊 Сервисов всего: {total}")
            print(f"✅ Здоровых: {healthy}")
            print(f"❌ Недоступных: {total - healthy}")

            if healthy > 0:
                print("\n🟢 Доступные сервисы:")
                for name, info in services.get("services", {}).items():
                    status = "🟢" if info.get("status") == "healthy" else "🔴"
                    print(f"  {status} {name}: {info.get('url', 'N/A')}")

            return healthy > 0
        else:
            print(f"❌ Ошибка получения статуса сервисов: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка проверки сервисов: {e}")
        return False

def test_basic_functionality():
    """Тестирование базовой функциональности"""
    print("\n🔍 Тестирование базовой функциональности...")

    # Тест регистрации
    test_user = {
        "email": "simple_test@example.com",
        "full_name": "Простой Тест",
        "password": "test123",
        "phone": "+7-999-111-22-33",
        "role": "client"
    }

    try:
        print("📝 Тестирование регистрации...")
        response = requests.post(f"{BASE_URL}/auth/register", json=test_user, timeout=TIMEOUT)
        if response.status_code == 200:
            print("✅ Регистрация успешна")
        elif "already exists" in response.text.lower():
            print("ℹ️  Пользователь уже существует")
        else:
            print(f"⚠️  Регистрация: статус {response.status_code}")

        # Тест входа
        print("🔐 Тестирование входа...")
        login_data = {"username": test_user["email"], "password": test_user["password"]}
        response = requests.post(f"{BASE_URL}/auth/token", data=login_data, timeout=TIMEOUT)
        if response.status_code == 200:
            tokens = response.json()
            token = tokens.get("access_token")
            print("✅ Вход успешен, токен получен")

            # Тест создания автомобиля
            headers = {"Authorization": f"Bearer {token}"}
            test_vehicle = {
                "make": "Test",
                "model": "Car",
                "year": 2024,
                "price": 1000000.00,
                "vin": f"TEST{int(time.time())}",
                "color": "Синий",
                "mileage": 0,
                "fuel_type": "Бензин",
                "transmission": "Автомат"
            }

            print("🚗 Тестирование создания автомобиля...")
            response = requests.post(f"{BASE_URL}/vehicles", json=test_vehicle, headers=headers, timeout=TIMEOUT)
            if response.status_code in [200, 201]:
                print("✅ Автомобиль создан")
            else:
                print(f"⚠️  Создание автомобиля: статус {response.status_code}")

        else:
            print(f"⚠️  Вход: статус {response.status_code}")

    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")

def main():
    """Основная функция"""
    print("🚗 ПРОСТОЙ ТЕСТ СИСТЕМЫ АВТОСАЛОНА")
    print("=" * 50)

    # Быстрая проверка подключения
    print("⏳ Быстрая проверка подключения...")
    if not test_connection():
        print("\n❌ Система недоступна!")
        print("\n🔧 Инструкция по запуску:")
        print("1. Запустите Docker Desktop")
        print("2. Выполните: docker-compose up --build -d")
        print("3. Подождите 2-3 минуты пока сервисы запустятся")
        print("4. Запустите тест снова: python simple_test.py")
        print("\n💡 Для полного тестирования: python comprehensive_test.py")
        sys.exit(1)

    # Проверка сервисов
    if not test_services():
        print("\n⚠️  Некоторые сервисы недоступны, но продолжаем тестирование...")

    # Базовое тестирование
    test_basic_functionality()

    print("\n" + "=" * 50)
    print("✅ Простое тестирование завершено!")
    print("\n📖 Для полного тестирования запустите:")
    print("   python comprehensive_test.py")

if __name__ == "__main__":
    main()