from sqlalchemy import select

from app.models.user import UserORM
from app.repositories.base import BaseRepository
from app.schemas.user import UserRole


class UserRepository(BaseRepository[UserORM]):
    model = UserORM

    def create(
        self,
        email: str,
        login: str,
        password: str,
        role: UserRole = UserRole.EMPLOYEE,
    ) -> UserORM:
        new = UserORM(email=email, login=login, password=password, role=role)
        self.db.add(new)
        return new

    def get_by_login(self, login: str) -> UserORM | None:
        query = select(UserORM).where(UserORM.login == login)
        return self.db.scalars(query).first()
