# Заглушка для импорта
# В реальности используется auth из общего shared модуля

class AuthUtils:
    @staticmethod
    def verify_token(token: str):
        # Заглушка
        return {"user_id": 1, "role": "admin"}