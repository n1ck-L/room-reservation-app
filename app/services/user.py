from sqlalchemy.orm import Session

from app.core.settings import hash_password
from app.repositories.user import UserRepository
from app.schemas.user import (
    UserCreateSchema,
    UserRole,
    UserSchema,
    UserUpdateSchema,
)
from app.services.exceptions import NotFoundError
from app.core.settings import settings


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = UserRepository(db)

    def list_users(self) -> list[UserSchema]:
        users = self.repository.get_all()
        return [UserSchema.model_validate(user) for user in users]

    def create_user(self, user_create: UserCreateSchema) -> UserSchema:
        existing = self.repository.get_by_login(user_create.login)
        if existing is not None:
            raise ValueError("Пользователь с таким login уже существует")

        user_orm = self.repository.create(
            email=user_create.email,
            login=user_create.login,
            password=hash_password(user_create.password.get_secret_value()),
            role=user_create.role,
        )
        self.db.commit()
        return UserSchema.model_validate(user_orm)

    def update_user(self, user_id: str, user_update: UserUpdateSchema) -> UserSchema:
        user_for_update = self.repository.get_by_id(id=user_id)
        if user_for_update is None:
            raise NotFoundError("Пользователь", user_id)

        if user_update.email is not None:
            user_for_update.email = user_update.email
        if user_update.login is not None:
            user_for_update.login = user_update.login
        if user_update.password is not None:
            user_for_update.password = hash_password(
                user_update.password.get_secret_value()
            )
        if user_update.role is not None:
            user_for_update.role = user_update.role

        self.db.commit()
        return UserSchema.model_validate(user_for_update)

    def delete_user(self, user_id: str) -> None:
        user_to_delete = self.repository.get_by_id(id=user_id)
        if user_to_delete is None:
            raise NotFoundError("Пользователь", user_id)

        self.repository.delete(user_to_delete)
        self.db.commit()

    def ensure_default_admin(self) -> None:
        if not settings.SEED_DEFAULT_ADMIN:
            return

        if self.repository.get_by_login(settings.DEFAULT_ADMIN_LOGIN) is not None:
            return

        self.repository.create(
            email=settings.DEFAULT_ADMIN_EMAIL,
            login=settings.DEFAULT_ADMIN_LOGIN,
            password=hash_password(settings.DEFAULT_ADMIN_PASSWORD.get_secret_value()),
            role=UserRole.ADMIN,
        )
        self.db.commit()
