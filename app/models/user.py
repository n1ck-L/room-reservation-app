from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UserORM(Base):
    __tablename__ = "users"

    email: Mapped[str]
    login: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
