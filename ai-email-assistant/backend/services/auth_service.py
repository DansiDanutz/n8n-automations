"""
Authentication service for AI Email Assistant.
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
import os

logger = logging.getLogger(__name__)

class AuthService:
    """Service for user authentication and authorization."""
    
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Mock user database (in production, use real database)
        self.users = {
            "demo@example.com": {
                "id": "user_123",
                "email": "demo@example.com", 
                "hashed_password": self.get_password_hash("demopass123"),
                "is_active": True,
                "created_at": datetime.utcnow()
            }
        }
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash."""
        return self.pwd_context.hash(password)
    
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password."""
        try:
            user = self.users.get(email)
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
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
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
    
    async def register_user(self, email: str, password: str, first_name: str, last_name: str) -> Dict[str, Any]:
        """Register new user."""
        try:
            if email in self.users:
                raise ValueError("User already exists")
            
            user_id = f"user_{len(self.users) + 1}"
            hashed_password = self.get_password_hash(password)
            
            user = {
                "id": user_id,
                "email": email,
                "hashed_password": hashed_password,
                "first_name": first_name,
                "last_name": last_name,
                "is_active": True,
                "created_at": datetime.utcnow()
            }
            
            self.users[email] = user
            logger.info(f"User {email} registered successfully")
            
            return user
            
        except Exception as e:
            logger.error(f"User registration failed: {e}")
            raise