"""
Authentication service for AI Email Assistant.
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash
import os

logger = logging.getLogger(__name__)


def required_secret(name: str, minimum_length: int) -> str:
    value = os.getenv(name, "")
    if len(value) < minimum_length:
        raise RuntimeError(f"{name} must be at least {minimum_length} characters")
    return value


class AuthService:
    """Service for user authentication and authorization."""
    
    def __init__(self):
        self.secret_key = required_secret("JWT_SECRET_KEY", 32)
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.password_hash = PasswordHash.recommended()
        
        self.users = {}
        admin_email = os.getenv("ADMIN_EMAIL", "").strip().lower()
        admin_password = os.getenv("ADMIN_PASSWORD", "")
        if bool(admin_email) != bool(admin_password):
            raise RuntimeError("ADMIN_EMAIL and ADMIN_PASSWORD must be configured together")
        if admin_email:
            if len(admin_password) < 12:
                raise RuntimeError("ADMIN_PASSWORD must be at least 12 characters")
            self.users[admin_email] = {
                "id": "admin",
                "email": admin_email,
                "hashed_password": self.get_password_hash(admin_password),
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
            }
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return self.password_hash.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash."""
        return self.password_hash.hash(password)
    
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password."""
        try:
            user = self.users.get(email.strip().lower())
            if not user:
                return None
            
            if not self.verify_password(password, user["hashed_password"]):
                return None
                
            return user
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return None
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return user data."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            email: str = payload.get("sub")
            if email is None:
                return None
                
            user = self.users.get(email)
            if user is None:
                return None
                
            return user
            
        except jwt.PyJWTError:
            return None
