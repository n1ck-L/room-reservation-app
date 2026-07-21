from app.models.user import UserORM
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[UserORM]):
    model = UserORM

    def create(self, email: str, login: str, password: str) -> UserORM:
        new = UserORM(email=email, login=login, password=password)
        self.db.add(new)
        return new
