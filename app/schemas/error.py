from pydantic import BaseModel


class ErrorSchema(BaseModel):
    detail: str


class ValidationErrorItemSchema(BaseModel):
    loc: list[str | int]
    msg: str
    type: str


class ValidationErrorSchema(BaseModel):
    detail: list[ValidationErrorItemSchema]
