#!/usr/bin/env python3
"""
Простой тест-раннер для системы автосалона
"""

import subprocess
import sys
import os

def run_test():
    """Запуск теста через subprocess"""
    try:
        # Меняем директорию на текущую
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        # Запускаем тест
        result = subprocess.run([
            sys.executable, "basic_test.py"
        ], capture_output=True, text=True, timeout=60)

        print("=== TEST COMPLETED ===")
        print("STDOUT:")
        print(result.stdout)
        print("STDERR:")
        print(result.stderr)
        print(f"Return code: {result.returncode}")

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("TIMEOUT Test hung")
        return False
    except Exception as e:
        print(f"ERROR starting test: {e}")
        return False

if __name__ == "__main__":
    print("Запуск тест-раннера...")
    success = run_test()
    if success:
        print("Тест прошел успешно")
        sys.exit(0)
    else:
        print("Тест провалился")
        sys.exit(1)