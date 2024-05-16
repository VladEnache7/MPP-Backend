from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
# import pyodbc

import models

# from sqlalchemy.ext.declarative import

# Create a connection to the database
URL_DATABASE = 'sqlite:///./entities.db'

# initialize a new engine that will interface with the database specified by URL_DATABASE
engine = create_engine(URL_DATABASE, connect_args={'check_same_thread': False})
# engine = create_engine(
# "mssql+pyodbc://vladai:pAr0!4mE4@sqlserver-movies-germany.database.windows.net,1433/sqldb-movies-germanysqldb-movies-germany?driver=ODBC+Driver+18+for+SQL+Server")

# Create a session to interact with the database
SessionLocalMovies = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Create a base class for our classes
Base_database = declarative_base()
