from datetime import timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm



from app.core.dependencies import (
    CurrentUser,
    SessionDep,
)
from app.core.security import create_access_token
from app.core.config import get_settings
from app.core.errors import BusinessException, ErrorCode


from app.domains.user import repository
from app.domains.user.schemas import (
    Token,
    UserPublic,
)




settings = get_settings()
router = APIRouter()


@router.post("/login/access-token")
async def login_access_token(
    session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = await repository.authenticate(
        session=session, email=form_data.username, password=form_data.password
    )
    if not user:
        raise BusinessException(
            code=ErrorCode.AUTH_INVALID_CREDENTIALS,
            detail="Incorrect email or password"
        )
    elif not user.is_active:
        raise BusinessException(
            code=ErrorCode.AUTH_INACTIVE_USER,
            detail="Inactive user"
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=create_access_token(
            user.id, expires_delta=access_token_expires
        )
    )


@router.post("/login/test-token", response_model=UserPublic)
async def test_token(current_user: CurrentUser) -> Any:
    """
    Test access token
    """
    return current_user




