# backend/services/user_service.py
import jwt
import bcrypt
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# В продакшене использовать переменную окружения
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

class UserService:
    """Сервис для работы с пользователями"""
    
    def __init__(self):
        # В продакшене использовать базу данных
        self.users: Dict[str, Dict] = {}  # {user_id: {username, password_hash, settings}}
        self.tokens: Dict[str, str] = {}  # {token: user_id}
    
    async def register_user(self, username: str, password: str) -> Dict:
        """Регистрация нового пользователя"""
        try:
            # Проверяем, существует ли пользователь
            for user in self.users.values():
                if user['username'] == username:
                    raise ValueError("Username already exists")
            
            # Хешируем пароль
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            # Создаём пользователя
            user_id = str(uuid.uuid4())
            self.users[user_id] = {
                'username': username,
                'password_hash': password_hash,
                'created_at': datetime.now(),
                'settings': {}
            }
            
            # Генерируем токен
            token = self._generate_token(user_id)
            self.tokens[token] = user_id
            
            logger.info(f"User registered: {username}")
            return {'user_id': user_id, 'token': token}
            
        except Exception as e:
            logger.error(f"Error registering user: {str(e)}")
            raise
    
    async def login_user(self, username: str, password: str) -> Dict:
        """Авторизация пользователя"""
        try:
            # Ищем пользователя
            user_id = None
            user_data = None
            
            for uid, data in self.users.items():
                if data['username'] == username:
                    user_id = uid
                    user_data = data
                    break
            
            if not user_data:
                raise ValueError("Invalid credentials")
            
            # Проверяем пароль
            if not bcrypt.checkpw(password.encode('utf-8'), user_data['password_hash']):
                raise ValueError("Invalid credentials")
            
            # Генерируем токен
            token = self._generate_token(user_id)
            self.tokens[token] = user_id
            
            logger.info(f"User logged in: {username}")
            return {'user_id': user_id, 'token': token}
            
        except Exception as e:
            logger.error(f"Error logging in: {str(e)}")
            raise
    
    async def verify_token(self, token: str) -> str:
        """Проверить токен и вернуть user_id"""
        try:
            if token not in self.tokens:
                # Пытаемся декодировать JWT
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                user_id = payload.get('user_id')
                
                # Проверяем срок действия
                exp = payload.get('exp')
                if datetime.fromtimestamp(exp) < datetime.now():
                    raise ValueError("Token expired")
                
                return user_id
            
            return self.tokens[token]
            
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            raise ValueError("Invalid token")
    
    async def get_user_settings(self, user_id: str) -> Dict:
        """Получить настройки пользователя"""
        if user_id not in self.users:
            raise ValueError("User not found")
        
        return self.users[user_id].get('settings', {})
    
    async def save_user_settings(self, user_id: str, settings: Dict):
        """Сохранить настройки пользователя"""
        if user_id not in self.users:
            raise ValueError("User not found")
        
        self.users[user_id]['settings'] = settings
        logger.info(f"Settings saved for user {user_id}")
    
    def _generate_token(self, user_id: str) -> str:
        """Генерировать JWT токен"""
        payload = {
            'user_id': user_id,
            'exp': datetime.now() + timedelta(hours=TOKEN_EXPIRE_HOURS),
            'iat': datetime.now()
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return token
    
    async def logout_user(self, token: str):
        """Выход пользователя"""
        if token in self.tokens:
            del self.tokens[token]
            logger.info("User logged out")
