from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.auth import LoginSchema, TokenRevokeSchema, TokenSchema, TokenRefreshSchema
from app.services.auth import AuthService
from app.api.dependencies import get_auth_service

router = APIRouter(prefix="/auth/tokens")


@router.post("")
def login(payload: LoginSchema,
          auth_service: AuthService = Depends(get_auth_service)) -> TokenSchema:
    try:
        return auth_service.login(payload=payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    

@router.post("/refresh")
def refresh(payload: TokenRefreshSchema,
            auth_service: AuthService = Depends(get_auth_service)) -> TokenSchema:
    try:
        return auth_service.refresh_token(token_data=payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post("/revoke")
def refresh(payload: TokenRevokeSchema,
            auth_service: AuthService = Depends(get_auth_service)) -> None:
    auth_service.revoke_token(token_data=payload)