import uuid
from typing import Any, Dict, Optional, Type
from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from fastapi_users.db import BaseUserDatabase
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.usuario import Usuario

SECRET = "SECRET_KEY_MOCK"  # TODO: Inject via environment variable

class SQLAlchemyUserDatabaseSync(BaseUserDatabase[Usuario, uuid.UUID]):
    """Custom synchronous database adapter for FastAPI Users.
    
    Interfaces with a synchronous SQLAlchemy Session while exposing
    the asynchronous architecture required by the user manager.
    """
    def __init__(self, session: Session, user_model: Type[Usuario]):
        self.session = session
        self.user_model = user_model

    async def get(self, id: uuid.UUID) -> Optional[Usuario]:
        return self.session.get(self.user_model, id)

    async def get_by_email(self, email: str) -> Optional[Usuario]:
        # Using getattr satisfies Pylance type checking for instrumented attributes
        email_attr = getattr(self.user_model, "email")
        stmt = select(self.user_model).where(email_attr.ilike(email))
        return self.session.execute(stmt).scalar_one_or_none()

    async def get_by_oauth_account(self, oauth: str, account_id: str) -> Optional[Usuario]:
        return None

    async def create(self, create_dict: Dict[str, Any]) -> Usuario:
        user = self.user_model(**create_dict)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    async def update(self, user: Usuario, update_dict: Dict[str, Any]) -> Usuario:
        for key, value in update_dict.items():
            setattr(user, key, value)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    async def delete(self, user: Usuario) -> None:
        self.session.delete(user)
        self.session.commit()

def get_user_db(session: Session = Depends(get_db)):
    yield SQLAlchemyUserDatabaseSync(session, Usuario)

class UserManager(UUIDIDMixin, BaseUserManager[Usuario, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: Usuario, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(self, user: Usuario, token: str, request: Optional[Request] = None):
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(self, user: Usuario, token: str, request: Optional[Request] = None):
        print(f"Verification requested for user {user.id}. Verification token: {token}")

async def get_user_manager(user_db: SQLAlchemyUserDatabaseSync = Depends(get_user_db)):
    yield UserManager(user_db)

bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[Usuario, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

current_active_user = fastapi_users.current_user(active=True)