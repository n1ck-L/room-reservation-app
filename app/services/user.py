from sqlalchemy.orm import Session

from app.core.settings import hash_password
from app.repositories.user import UserRepository
from app.schemas.user import UserCreateSchema, UserSchema, UserUpdateSchema
from app.services.exceptions import NotFoundError


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = UserRepository(db)

    def list_users(self) -> list[UserSchema]:
        # проверку что роль = admin
        users = self.repository.get_all()
        return [UserSchema.model_validate(user) for user in users]

    def create_user(self, user_create: UserCreateSchema) -> UserSchema:
        # проверку что роль = admin
        existing = self.repository.get_by_login(user_create.login)
        if existing is not None:
            raise ValueError("Пользователь с таким login уже существует")

        user_orm = self.repository.create(
            email=user_create.email,
            login=user_create.login,
            password=hash_password(user_create.password.get_secret_value()),
        )
        self.db.commit()
        return UserSchema.model_validate(user_orm)

    def update_user(
        self, user_id: str, user_update: UserUpdateSchema
    ) -> UserSchema:
        # проверку что роль = admin
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

        self.db.commit()
        return UserSchema.model_validate(user_for_update)

    def delete_user(self, user_id: str) -> None:
        # проверку что роль = admin
        user_to_delete = self.repository.get_by_id(id=user_id)
        if user_to_delete is None:
            raise NotFoundError("Пользователь", user_id)

        self.repository.delete(user_to_delete)
        self.db.commit()
