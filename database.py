from typing import Annotated
from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import models

# URL for the database connection
URL_DATABASE = 'sqlite:///./entities.db'

# This is a new engine that will interface with the database specified by URL_DATABASE.
# This engine uses SQLite and connects to a local file named 'entities.db'
engine = create_engine(URL_DATABASE, connect_args={'check_same_thread': False})

# This is a session to interact with the database.
# This session is not autocommitting, meaning changes won't be persisted automatically
# Changes also won't be flushed to the database automatically
SessionLocalMovies = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# This is a base class for our models
# This base class contains a metaclass that produces appropriate Table objects and makes the appropriate mapper() calls
Base_database = declarative_base()
