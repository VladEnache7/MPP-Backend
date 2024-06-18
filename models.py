from database import Base_database
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime


class User(Base_database):
    """
    User model for the database. Represents a user with a unique username and hashed password.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashedPassword = Column(String)
    nrMovies = Column(Integer, default=0)
    nrCharacters = Column(Integer, default=0)

    def to_dict(self):
        """
        Convert the User object to a dictionary.
        :return: A dictionary representation of the User object.
        """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Movie(Base_database):
    """
    Movie model for the database. Represents a movie with unique name.
    """
    __tablename__ = 'movies3'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)
    year = Column(Integer)
    duration = Column(String)
    genre = Column(String)
    description = Column(Integer)
    nrCharacters = Column(Integer, default=0)
    editorId = Column(Integer, default=None)

    def to_dict(self):
        """
        Convert the Movie object to a dictionary.
        :return: A dictionary representation of the Movie object.
        """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Character(Base_database):
    """
    Character model for the database. Represents a character in a movie.
    """
    __tablename__ = 'characters'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    movieName = Column(String)
    description = Column(String)
    editorId = Column(Integer, default=None)

    def to_dict(self):
        """
        Convert the Character object to a dictionary.
        :return: A dictionary representation of the Character object.
        """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
