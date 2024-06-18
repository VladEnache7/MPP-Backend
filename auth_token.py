from datetime import datetime, timedelta
from fastapi import HTTPException, status
from jose import JWTError, jwt
from typing import Optional
from passlib.context import CryptContext

# Secret key used for JWT encoding and decoding
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
# Algorithm used for JWT encoding and decoding
ALGORITHM = "HS256"
# Duration in minutes for which the access token is valid
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# CryptContext instance for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create a JWT access token.

    :param data: The data to be included in the token.
    :param expires_delta: The duration for which the token is valid. If not provided, defaults to 15 minutes.
    :return: The encoded JWT token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str):
    """
    Decode a JWT access token.

    :param token: The JWT token to decode.
    :return: The decoded JWT token.
    :raises HTTPException: If the token cannot be decoded.
    """
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_password(plain_password, hashed_password):
    """
    Verify a password against a hashed password.

    :param plain_password: The plain text password to verify.
    :param hashed_password: The hashed password to verify against.
    :return: True if the password is correct, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """
    Hash a password.

    :param password: The password to hash.
    :return: The hashed password.
    """
    return pwd_context.hash(password)
