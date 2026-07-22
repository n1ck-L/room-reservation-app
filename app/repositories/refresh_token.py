from datetime import datetime

from sqlalchemy import select

from app.repositories.base import BaseRepository
from app.models.refresh_token import RefreshTokenORM


class RefreshTokenRepository(BaseRepository[RefreshTokenORM]):
    model = RefreshTokenORM

    def create(
        self, user_id: str, token: str, expires_at: datetime, is_revoked: bool
    ) -> RefreshTokenORM:
        new = RefreshTokenORM(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            is_revoked=is_revoked,
        )
        self.db.add(new)
        return new

    def get_by_token(self, token: str) -> RefreshTokenORM | None:
        query = select(RefreshTokenORM).where(RefreshTokenORM.token == token)
        return self.db.scalars(query).first()
