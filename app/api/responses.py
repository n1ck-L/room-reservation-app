from fastapi import status

from app.schemas.error import ErrorSchema, ValidationErrorSchema

RESP_401 = {
    status.HTTP_401_UNAUTHORIZED: {
        "model": ErrorSchema,
        "description": "Unauthorized",
    }
}

RESP_403 = {
    status.HTTP_403_FORBIDDEN: {
        "model": ErrorSchema,
        "description": "Not enough rights",
    }
}

RESP_404 = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorSchema,
        "description": "Resource was not found",
    }
}

RESP_409 = {
    status.HTTP_409_CONFLICT: {
        "model": ErrorSchema,
        "description": "Data conflict",
    }
}

RESP_422 = {
    status.HTTP_422_UNPROCESSABLE_CONTENT: {
        "model": ValidationErrorSchema,
        "description": "Validation Error",
    }
}

RESP_204 = {
    status.HTTP_204_NO_CONTENT: {
        "description": "Successful Response",
    }
}


def combine(*response_dicts: dict) -> dict:
    merged: dict = {}
    for response_dict in response_dicts:
        merged.update(response_dict)
    return merged


AUTH = combine(RESP_401, RESP_422)
ADMIN = combine(RESP_401, RESP_403, RESP_422)
