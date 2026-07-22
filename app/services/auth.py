from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.schemas.settings import SettingsSchema
from app.core.settings import (
    create_access_token,
    create_refresh_token,
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


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.refresh_repository = RefreshTokenRepository(db)
        self.user_repository = UserRepository(db)

    def login(self, payload: LoginSchema) -> TokenSchema:
        user = self.user_repository.get_by_login(payload.login)
        if user is None:
            raise ValueError("Неверный login или password")

        if not verify_password(
            plain=payload.password.get_secret_value(), hashed=user.password
        ):
            raise ValueError("Неверный login или password")

        token_data = {"sub": user.id}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        expires_at = datetime.now(timezone.utc) + timedelta(
            days=SettingsSchema().REFRESH_TOKEN_EXPIRE_DAYS
        )

        self.refresh_repository.create(
            user_id=user.id,
            token=refresh_token,
            expires_at=expires_at,
            is_revoked=False,
        )
        self.db.commit()

        return TokenSchema(
            access_token=access_token, refresh_token=refresh_token
        )

    def refresh_token(self, token_data: TokenRefreshSchema) -> TokenSchema:
        payload = decode_refresh_token(token=token_data.refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("Неверный тип токена")

        refresh_orm = self.refresh_repository.get_by_token(
            token_data.refresh_token
        )
        if refresh_orm is None or refresh_orm.is_revoked:
            raise ValueError("Refresh-токен недействителен")

        if refresh_orm.expires_at.replace(tzinfo=timezone.utc) < datetime.now(
            timezone.utc
        ):
            raise ValueError("Refresh-токен истёк")

        user_id = payload.get("sub")
        access_token_data = {"sub": user_id}
        new_access = create_access_token(access_token_data)
        return TokenSchema(
            access_token=new_access, refresh_token=token_data.refresh_token
        )

    def revoke_token(self, token_data: TokenRevokeSchema) -> None:
        refresh_orm = self.refresh_repository.get_by_token(
            token_data.refresh_token
        )
        if refresh_orm is None:
            return

        refresh_orm.is_revoked = True
        self.db.commit()
