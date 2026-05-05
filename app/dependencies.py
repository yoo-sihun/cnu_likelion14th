"""
JWT 기반 현재 유저 조회 의존성.

라우터에서 Depends(get_current_user)로 사용한다.
"""

import os

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.repositories import user_repo

load_dotenv()
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증에 실패했습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = user_repo.get_user_by_id(db, int(user_id))
    if user is None:
        raise credentials_exception
    return user