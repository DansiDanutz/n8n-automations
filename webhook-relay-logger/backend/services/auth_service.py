"""
Authentication service for Webhook Relay & Logger.
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
        self.secret_key = os.getenv("JWT_SECRET_KEY", "webhook-relay-secret-change-in-production")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Mock user database (in production, use real database)
        self.users = {
            "demo@webhook.dev": {
                "id": "user_webhook_123",
                "email": "demo@webhook.dev", 
                "hashed_password": self.get_password_hash("webhook123"),
                "name": "Demo User",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "plan": "pro",  # free, pro, enterprise
                "rate_limit": 1000  # requests per hour
            },
            "test@example.com": {
                "id": "user_test_456",
                "email": "test@example.com",
                "hashed_password": self.get_password_hash("testpass123"),
                "name": "Test User",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "plan": "free",
                "rate_limit": 100
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
            if not user or not user["is_active"]:
                return None
            
            if not self.verify_password(password, user["hashed_password"]):
                return None
                
            # Remove password from returned user data
            user_data = user.copy()
            user_data.pop("hashed_password", None)
            return user_data
            
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
            if user is None or not user["is_active"]:
                return None
            
            # Remove password from returned user data
            user_data = user.copy()
            user_data.pop("hashed_password", None)
            return user_data
            
        except jwt.PyJWTError as e:
            logger.warning(f"Token verification failed: {e}")
            return None
    
    async def register_user(self, email: str, password: str, name: str) -> Dict[str, Any]:
        """Register new user."""
        try:
            if email in self.users:
                raise ValueError("User already exists")
            
            user_id = f"user_{len(self.users) + 1}_{email.split('@')[0]}"
            hashed_password = self.get_password_hash(password)
            
            user = {
                "id": user_id,
                "email": email,
                "hashed_password": hashed_password,
                "name": name,
                "is_active": True,
                "created_at": datetime.utcnow(),
                "plan": "free",  # Default to free plan
                "rate_limit": 100  # Free plan limit
            }
            
            self.users[email] = user
            logger.info(f"User {email} registered successfully")
            
            # Return user data without password
            user_data = user.copy()
            user_data.pop("hashed_password", None)
            return user_data
            
        except Exception as e:
            logger.error(f"User registration failed: {e}")
            raise
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            for user in self.users.values():
                if user["id"] == user_id:
                    user_data = user.copy()
                    user_data.pop("hashed_password", None)
                    return user_data
            return None
        except Exception as e:
            logger.error(f"Failed to get user by ID: {e}")
            return None
    
    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update user information."""
        try:
            user_email = None
            for email, user in self.users.items():
                if user["id"] == user_id:
                    user_email = email
                    break
            
            if not user_email:
                raise ValueError("User not found")
            
            # Apply updates (excluding sensitive fields)
            allowed_updates = ["name", "plan", "rate_limit", "is_active"]
            for key, value in updates.items():
                if key in allowed_updates:
                    self.users[user_email][key] = value
            
            # Handle password update separately
            if "password" in updates:
                self.users[user_email]["hashed_password"] = self.get_password_hash(updates["password"])
            
            logger.info(f"Updated user {user_id}")
            
            # Return updated user data
            user_data = self.users[user_email].copy()
            user_data.pop("hashed_password", None)
            return user_data
            
        except Exception as e:
            logger.error(f"User update failed: {e}")
            raise
    
    async def check_rate_limit(self, user_id: str) -> Dict[str, Any]:
        """Check user's rate limit status."""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                raise ValueError("User not found")
            
            # In a real implementation, you'd check against actual usage
            # For demo purposes, return static values
            rate_limit = user.get("rate_limit", 100)
            current_usage = 0  # Would be calculated from actual requests
            
            return {
                "rate_limit": rate_limit,
                "current_usage": current_usage,
                "remaining": rate_limit - current_usage,
                "reset_time": (datetime.utcnow() + timedelta(hours=1)).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            raise
    
    async def deactivate_user(self, user_id: str):
        """Deactivate user account."""
        try:
            await self.update_user(user_id, {"is_active": False})
            logger.info(f"Deactivated user {user_id}")
        except Exception as e:
            logger.error(f"User deactivation failed: {e}")
            raise
    
    async def list_users(self, admin_user_id: str = None) -> List[Dict[str, Any]]:
        """List all users (admin only)."""
        try:
            # In production, check if admin_user_id has admin privileges
            users_list = []
            for user in self.users.values():
                user_data = user.copy()
                user_data.pop("hashed_password", None)
                users_list.append(user_data)
            
            return users_list
            
        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            raise