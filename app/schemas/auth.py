from pydantic import BaseModel, ConfigDict, SecretStr

class LoginSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    login: str
    password: SecretStr


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefreshSchema(BaseModel):
    refresh_token: str


class TokenRevokeSchema(BaseModel):
    refresh_token: str