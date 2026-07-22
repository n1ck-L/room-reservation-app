from enum import StrEnum

from pydantic import BaseModel, ConfigDict, SecretStr


class UserRole(StrEnum):
    ADMIN = "admin"
    EMPLOYEE = "employee"


class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    login: str
    password: SecretStr
    role: UserRole


class UserCreateSchema(BaseModel):
    email: str
    login: str
    password: SecretStr
    role: UserRole = UserRole.EMPLOYEE


class UserUpdateSchema(BaseModel):
    email: str | None = None
    login: str | None = None
    password: SecretStr | None = None
    role: UserRole | None = None


class CurrentUserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: UserRole
