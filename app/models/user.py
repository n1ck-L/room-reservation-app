from sqlalchemy.orm import Mapped

from app.models.base import Base


class UserORM(Base):
    __tablename__ = "users"

    email: Mapped[str]
    login: Mapped[str]
    password: Mapped[str]