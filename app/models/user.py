from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.schemas.user import UserRole


class UserORM(Base):
    __tablename__ = "users"

    email: Mapped[str]
    login: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    role: Mapped[UserRole] = mapped_column(default=UserRole.EMPLOYEE)
