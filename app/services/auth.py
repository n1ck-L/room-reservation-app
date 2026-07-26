from datetime import datetime, timedelta, timezone

from jose import JWTError
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.core.settings import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    verify_password,
)
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import UserRepository
from app.schemas.auth import (
    LoginSchema,
    TokenRefreshSchema,
    TokenRevokeSchema,
    TokenSchema,
)
from app.schemas.user import CurrentUserSchema
from app.services.exceptions import NotFoundError, UnauthorizedError


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.refresh_repository = RefreshTokenRepository(db)
        self.user_repository = UserRepository(db)

    def login(self, payload: LoginSchema) -> TokenSchema:
        user = self.user_repository.get_by_login(payload.login)
        if user is None:
            raise UnauthorizedError("Неверный login или password")

        if not verify_password(
            plain=payload.password.get_secret_value(), hashed=user.password
        ):
            raise UnauthorizedError("Неверный login или password")

        token_data = {"sub": user.id}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        self.refresh_repository.create(
            user_id=user.id,
            token=refresh_token,
            expires_at=expires_at,
            is_revoked=False,
        )
        self.db.commit()

        return TokenSchema(access_token=access_token, refresh_token=refresh_token)

    def refresh_token(self, token_data: TokenRefreshSchema) -> TokenSchema:
        try:
            payload = decode_refresh_token(token=token_data.refresh_token)
        except JWTError:
            raise UnauthorizedError("Невалидный refresh-токен")

        if payload.get("type") != "refresh":
            raise UnauthorizedError("Неверный тип токена")

        refresh_orm = self.refresh_repository.get_by_token(token_data.refresh_token)
        if refresh_orm is None or refresh_orm.is_revoked:
            raise UnauthorizedError("Refresh-токен недействителен")

        if refresh_orm.expires_at.replace(tzinfo=timezone.utc) < datetime.now(
            timezone.utc
        ):
            raise UnauthorizedError("Refresh-токен истёк")

        user_id = payload.get("sub")
        access_token_data = {"sub": user_id}
        new_access = create_access_token(access_token_data)
        return TokenSchema(
            access_token=new_access, refresh_token=token_data.refresh_token
        )

    def revoke_token(self, token_data: TokenRevokeSchema) -> None:
        refresh_orm = self.refresh_repository.get_by_token(token_data.refresh_token)
        if refresh_orm is None:
            return

        refresh_orm.is_revoked = True
        self.db.commit()

    def get_current_user(self, token: str) -> CurrentUserSchema:
        try:
            payload = decode_access_token(token)
        except JWTError:
            raise UnauthorizedError("Невалидный токен")

        if payload.get("type") != "access":
            raise UnauthorizedError("Неверный тип токена")

        user_id = payload.get("sub")
        if user_id is None:
            raise UnauthorizedError("Невалидный токен")

        user = self.user_repository.get_by_id(user_id)
        if user is None:
            raise NotFoundError("Пользователь", user_id)

        return CurrentUserSchema.model_validate(user)
