from pydantic import BaseModel, ConfigDict, SecretStr


class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    login: str
    password: SecretStr


class UserCreateSchema(BaseModel):
    email: str
    login: str
    password: SecretStr


class UserUpdateSchema(BaseModel):
    email: str | None = None
    login: str | None = None
    password: SecretStr | None = None
