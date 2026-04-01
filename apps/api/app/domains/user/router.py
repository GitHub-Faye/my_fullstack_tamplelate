import os
from typing import Annotated
from datetime import  timedelta

from app.core.security import get_password_hash
from fastapi import Depends, APIRouter, HTTPException, status


from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from .dependencies import get_current_active_user
from .schemas import User, Token
from .repository import fake_users_db, fake_hash_password, get_user
from app.core.security import verify_password, get_password_hash, create_access_token

router = APIRouter()


DUMMY_HASH = get_password_hash("dummypassword")
    

def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        verify_password(password, DUMMY_HASH)
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user





@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")



@router.get("/users/me/")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    return current_user