from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, get_user_repository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RefreshRequest, TokenPair
from app.schemas.user import UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(users: Annotated[UserRepository, Depends(get_user_repository)]) -> AuthService:
    return AuthService(users)


@router.post("/login", response_model=TokenPair)
def login(body: LoginRequest, auth: Annotated[AuthService, Depends(get_auth_service)]) -> TokenPair:
    return auth.login(body.email, body.password)


@router.post("/refresh", response_model=TokenPair)
def refresh(
    body: RefreshRequest, auth: Annotated[AuthService, Depends(get_auth_service)]
) -> TokenPair:
    return auth.refresh(body.refresh_token)


@router.get("/me", response_model=UserRead)
def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)
