from typing import Optional

from pydantic import BaseModel


# The code then defines two Pydantic models, MovieBase and MovieModel:
# Create a class that will be used to create a table in the database

class TokenData(BaseModel):
    username: str


class LoginRegisterModel(BaseModel):
    username: str
    hashedPassword: str


class MovieBase(BaseModel):
    name: str
    year: int
    duration: str
    genre: str
    description: str
    nrCharacters: int = 0
    editorId: Optional[int] = None


class MovieModel(MovieBase):
    id: int

    class Config:
        orm_mode = True
        from_attributes = True


class CharacterBase(BaseModel):
    name: str
    movieName: str
    description: str
    editorId: Optional[int] = None


class CharacterModel(CharacterBase):
    id: int

    class Config:
        orm_mode = True
        from_attributes = True
