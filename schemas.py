from typing import Optional
from pydantic import BaseModel


class TokenData(BaseModel):
    """
    Pydantic model for token data. Represents the data contained in a token.
    """
    username: str


class LoginRegisterModel(BaseModel):
    """
    Pydantic model for login and registration data. Represents the data required for a user to login or register.
    """
    username: str
    hashedPassword: str


class MovieBase(BaseModel):
    """
    Pydantic model for movie data. Represents the base data required for a movie.
    """
    name: str
    year: int
    duration: str
    genre: str
    description: str
    nrCharacters: int = 0
    editorId: Optional[int] = None


class MovieModel(MovieBase):
    """
    Pydantic model for movie data. Inherits from MovieBase and adds an id field.
    """
    id: int

    class Config:
        orm_mode = True
        from_attributes = True


class CharacterBase(BaseModel):
    """
    Pydantic model for character data. Represents the base data required for a character.
    """
    name: str
    movieName: str
    description: str
    editorId: Optional[int] = None


class CharacterModel(CharacterBase):
    """
    Pydantic model for character data. Inherits from CharacterBase and adds an id field.
    """
    id: int

    class Config:
        orm_mode = True
        from_attributes = True
