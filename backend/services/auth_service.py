# backend/services/auth_service.py
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Dict, Optional
from sqlalchemy.orm import Session
from database.models import User, Session as DBSession, UserSettings
from config import settings
import logging

logger = logging.getLogger(__name__)

class AuthService:
    """Real authentication service with database"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def register_user(self, username: str, password: str, email: Optional[str] = None) -> Dict:
        """Register new user"""
        try:
            # Check if user exists
            existing_user = self.db.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing_user:
                raise ValueError("Username or email already exists")
            
            # Hash password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            # Create user
            user = User(
                username=username,
                email=email,
                password_hash=password_hash.decode('utf-8'),
                is_active=True,
                created_at=datetime.utcnow()
            )
            self.db.add(user)
            self.db.flush()
            
            # Create default settings
            settings_obj = UserSettings(user_id=user.id)
            self.db.add(settings_obj)
            
            self.db.commit()
            
            # Generate token
            token = self._generate_token(user.id)
            self._save_session(user.id, token)
            
            logger.info(f"User registered: {username}")
            return {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'token': token
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Registration error: {str(e)}")
            raise
    
    async def login_user(self, username: str, password: str) -> Dict:
        """Login user"""
        try:
            # Find user
            user = self.db.query(User).filter(
                (User.username == username) | (User.email == username)
            ).first()
            
            if not user:
                raise ValueError("Invalid credentials")
            
            if not user.is_active:
                raise ValueError("Account is disabled")
            
            # Verify password
            if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                raise ValueError("Invalid credentials")
            
            # Update last login
            user.last_login = datetime.utcnow()
            self.db.commit()
            
            # Generate token
            token = self._generate_token(user.id)
            self._save_session(user.id, token)
            
            logger.info(f"User logged in: {username}")
            return {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'is_admin': user.is_admin,
                'token': token
            }
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            raise
    
    async def google_login(self, google_id: str, email: str, name: str) -> Dict:
        """Login/register via Google OAuth"""
        try:
            # Find or create user
            user = self.db.query(User).filter(User.google_id == google_id).first()
            
            if not user:
                # Create new user from Google
                user = User(
                    username=email.split('@')[0],  # Use email prefix as username
                    email=email,
                    google_id=google_id,
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                self.db.add(user)
                self.db.flush()
                
                # Create default settings
                settings_obj = UserSettings(user_id=user.id)
                self.db.add(settings_obj)
                
                self.db.commit()
                logger.info(f"New user created via Google: {email}")
            
            # Update last login
            user.last_login = datetime.utcnow()
            self.db.commit()
            
            # Generate token
            token = self._generate_token(user.id)
            self._save_session(user.id, token)
            
            return {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'is_admin': user.is_admin,
                'token': token
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Google login error: {str(e)}")
            raise
    
    async def verify_token(self, token: str) -> str:
        """Verify JWT token and return user_id"""
        try:
            # Check if session exists
            session = self.db.query(DBSession).filter(DBSession.token == token).first()
            
            if not session or session.expires_at < datetime.utcnow():
                raise ValueError("Invalid or expired token")
            
            # Decode JWT
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = payload.get('user_id')
            
            if not user_id:
                raise ValueError("Invalid token payload")
            
            # Update last activity
            session.last_activity = datetime.utcnow()
            self.db.commit()
            
            return user_id
            
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            raise
    
    async def logout_user(self, token: str):
        """Logout user by removing session"""
        try:
            session = self.db.query(DBSession).filter(DBSession.token == token).first()
            if session:
                self.db.delete(session)
                self.db.commit()
                logger.info(f"User logged out")
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            raise
    
    def _generate_token(self, user_id: str) -> str:
        """Generate JWT token"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_MINUTES // 60),
            'iat': datetime.utcnow()
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return token
    
    def _save_session(self, user_id: str, token: str):
        """Save session to database"""
        try:
            session = DBSession(
                user_id=user_id,
                token=token,
                expires_at=datetime.utcnow() + timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_MINUTES // 60),
                created_at=datetime.utcnow()
            )
            self.db.add(session)
            self.db.commit()
        except Exception as e:
            logger.error(f"Error saving session: {str(e)}")
            raise
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    async def create_admin_user(self, username: str, password: str, email: str) -> Dict:
        """Create admin user"""
        try:
            # Check if admin exists
            existing_admin = self.db.query(User).filter(User.is_admin == True).first()
            if existing_admin:
                raise ValueError("Admin user already exists")
            
            # Hash password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            # Create admin user
            user = User(
                username=username,
                email=email,
                password_hash=password_hash.decode('utf-8'),
                is_active=True,
                is_admin=True,
                created_at=datetime.utcnow()
            )
            self.db.add(user)
            self.db.flush()
            
            # Create settings
            settings_obj = UserSettings(user_id=user.id)
            self.db.add(settings_obj)
            
            self.db.commit()
            
            logger.info(f"Admin user created: {username}")
            return {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'is_admin': True
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Admin creation error: {str(e)}")
            raise
