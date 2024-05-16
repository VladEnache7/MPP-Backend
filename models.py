from database import Base_database
from sqlalchemy import Column, Integer, String, ForeignKey


class User(Base_database):
    __tablename__ = "Users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashedPassword = Column(String)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# Create a class that will be used to create a table in the database
class Movie(Base_database):
    # __tablename__ = 'movies3'
    __tablename__ = 'Movies'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)
    year = Column(Integer)
    duration = Column(String)
    genre = Column(String)
    description = Column(Integer)
    nrCharacters = Column(Integer, default=0)
    editorId = Column(Integer, ForeignKey("Users.id"))

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Character(Base_database):
    # __tablename__ = 'characters'
    __tablename__ = 'Characters'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    movieName = Column(String)
    description = Column(String)
    editorId = Column(Integer, ForeignKey("Users.id"))

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
