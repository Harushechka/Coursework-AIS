from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import os

# JWT settings (должны совпадать с auth-service)
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

class AuthUtils:
    """Authentication utilities for API Gateway (совместимо с auth-service)"""
    
    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """
        Verify JWT token and return payload.
        Compatible with auth-service token generation.
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # Проверяем, что токен не истек
            exp = payload.get("exp")
            if exp and datetime.utcnow() > datetime.fromtimestamp(exp):
                print("Token has expired")
                return None
                
            return payload
        except JWTError as e:
            print(f"JWT error: {e}")
            return None
        except Exception as e:
            print(f"Token verification error: {e}")
            return None
    
    @staticmethod
    def extract_user_info(payload: dict) -> dict:
        """
        Extract user information from JWT payload
        """
        return {
            "user_id": payload.get("sub") or payload.get("user_id"),
            "email": payload.get("email"),
            "role": payload.get("role", "client"),
            "permissions": payload.get("permissions", []),
            "exp": payload.get("exp")
        }
    
    @staticmethod
    def create_test_token(user_id: int = 1, email: str = "test@example.com", 
                         role: str = "client") -> str:
        """
        Create a test token for development purposes.
        In production, tokens should only come from auth-service.
        """
        data = {
            "sub": str(user_id),
            "user_id": user_id,
            "email": email,
            "role": role,
            "permissions": [],
            "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        }
        
        return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
    
    @staticmethod
    def validate_role_access(user_role: str, required_roles: list) -> bool:
        """
        Validate if user role has access to required roles
        """
        role_hierarchy = {
            "admin": ["admin", "manager", "client"],
            "manager": ["manager", "client"],
            "client": ["client"]
        }
        
        if user_role not in role_hierarchy:
            return False
            
        return any(required_role in role_hierarchy[user_role] 
                  for required_role in required_roles)
    
    @staticmethod
    def extract_token_from_header(authorization: str) -> Optional[str]:
        """
        Extract token from Authorization header
        """
        if not authorization:
            return None
            
        parts = authorization.split()
        
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None
            
        return parts[1]