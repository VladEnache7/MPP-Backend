import random
from datetime import datetime, timedelta
from typing import Annotated, List
from faker import Faker
from fastapi import Depends, HTTPException
from starlette import status

from models import Movie, Character, User
from database import SessionLocalMovies
from schemas import MovieBase, CharacterBase
from auth_token import create_access_token, verify_password, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES, \
    decode_access_token


def get_database():
    db = SessionLocalMovies()
    try:
        yield db
    finally:
        db.close()


db_dependency_movies = Annotated[Movie, Depends(get_database)]
db_dependency_characters = Annotated[Character, Depends(get_database)]
db_dependency_users = Annotated[User, Depends(get_database)]


# noinspection PyUnresolvedReferences
class EntitiesRepo:

    @staticmethod
    def get_all_movies(db: db_dependency_movies):
        """
        Get all movies from the database
        :param db: The database dependency that provides access to the movie database.
        :return: A list of movies from the database. Each movie is represented as a MovieModel.
        """
        movies = db.query(Movie).all()
        return movies

    @staticmethod
    def get_movies_names(db: db_dependency_movies):
        """
        Get the names of all movies from the database
        :param db: The database dependency that provides access to the movie database.
        :return: A list with all movie names.
        """
        movies = db.query(Movie).all()
        return [movie.name for movie in movies]

    @staticmethod
    def get_movies_skip_limit(db: db_dependency_movies, skip: int, limit: int):
        """
        Get movies from the database with pagination
        :param db: The database dependency that provides access to the movies database.
        :param skip: The number of movies to skip before starting to return the movies.
        :param limit: The maximum number of movies to return.
        :return: A list of movies from the database. Each movie is represented as a MovieModel.
        """
        movies = db.query(Movie).offset(skip).limit(limit).all()
        # movies = db.query(Movie).order_by(Movie.id).offset(skip).limit(limit).all()
        return movies

    @staticmethod
    def get_movie(db: db_dependency_movies, movie_id: int):
        """
        Get a movie from the database by its id or return a 404 error if the movie is not found.
        :param db: The database dependency that provides access to the movies database.
        :param movie_id: The id of the movie to get.
        :return: The movie with the specified id.
        :raises HTTPException: If the movie is not found.
        """
        movie = db.query(Movie).filter(Movie.id == movie_id).first()
        if movie is None:
            raise HTTPException(status_code=404, detail='Movie not found')
        return movie

    @staticmethod
    def add_movie(db: db_dependency_movies, movie: MovieBase):
        """
            Add a new movie to the database. If a movie with the same name already exists, return a 400 error.
            :param db: The database dependency that provides access to the movies database.
            :param movie: The movie data to add to the database.
            :return: The newly added movie.
            :raises HTTPException: If a movie with the same name already exists.
        """
        new_db_movie = Movie(**movie.dict())
        if db.query(Movie).filter(Movie.name == movie.name).first() is not None:
            raise HTTPException(status_code=400, detail='Movie already exists')
        db.add(new_db_movie)
        db.commit()
        db.refresh(new_db_movie)
        return new_db_movie

    @staticmethod
    def add_movies(db: db_dependency_movies, movies: List[MovieBase]):
        """
        Add a list of new movies to the database. If a movie with the same name already exists, it is skipped.
        :param db: The database dependency that provides access to the movies' database.
        :param movies: The list of movie data to add to the database.
        :return: A dictionary with the count of added and not added movies.
        :raises HTTPException: If a movie with the same name already exists.
        """
        db_movies = [Movie(**movie.dict()) for movie in movies]
        added_movies = []
        not_added_movies = []
        for movie in db_movies:
            # find if exists a movie with this name
            if db.query(Movie).filter(Movie.name == movie.name).first() is not None:
                not_added_movies.append(movie)
                continue
            added_movies.append(movie)
            db.add(movie)
            db.commit()
        db.commit()
        return {"added_movies": added_movies, "not_added_movies": not_added_movies}

    @staticmethod
    def update_movie(db: db_dependency_movies, movie_id: int, movie: MovieBase) -> Movie:
        """
        Update a movie in the database. If the movie does not exist, return a 404 error.
        :param db: The database dependency that provides access to the movies' database.
        :param movie_id: The id of the movie to update.
        :param movie: The new movie data.
        :return: The updated movie.
        :raises HTTPException: If the movie does not exist.
        """
        db_movie = db.query(Movie).filter(Movie.id == movie_id).first()
        if db_movie is None:
            raise HTTPException(status_code=404, detail='Movie not found')
        for key, value in movie.dict().items():
            if key != "nrCharacters" and key != "editorId":
                setattr(db_movie, key, value)
        db.commit()
        db.refresh(db_movie)
        return db_movie

    @staticmethod
    def delete_movie_by_id(db: db_dependency_movies, movie_id) -> None:
        """
        Delete a movie from the database by its id. If the movie does not exist, return a 404 error.
        :param db: The database dependency that provides access to the movie database.
        :param movie_id: The id of the movie to delete.
        :raises HTTPException: If the movie does not exist.
        """
        db_movie = db.query(Movie).filter(Movie.id == movie_id).first()
        if db_movie is None:
            raise HTTPException(status_code=404, detail='Movie not found')
        db.delete(db_movie)
        db.commit()

    @staticmethod
    def delete_movie_by_name(db: db_dependency_movies, movie_name) -> None:
        """
        Delete a movie from the database by its name. If the movie does not exist, return a 404 error.
        :param db: The database dependency that provides access to the movie database.
        :param movie_name: The name of the movie to delete.
        :raises HTTPException: If the movie does not exist.
        """
        db_movie = db.query(Movie).filter(Movie.name == movie_name).first()
        if db_movie is None:
            raise HTTPException(status_code=404, detail='Movie not found')
        db.delete(db_movie)
        db.commit()

    @staticmethod
    def delete_duplicates(db: db_dependency_movies) -> List[Movie]:
        """
        Delete duplicate movies from the database.
        :param db: The database dependency that provides access to the movie database.
        :return: A list of deleted movies.
        """
        deleted_movies = []
        movies = db.query(Movie).all()
        movie_names = [movie.name for movie in movies]
        for movie in movies:
            if movie_names.count(movie.name) > 1:
                deleted_movies.append(movie)
                db.delete(movie)
                movie_names.remove(movie.name)
        db.commit()
        return deleted_movies

    @staticmethod
    def generate_and_add_movies(db: db_dependency_movies, count: int) -> List[MovieBase]:
        """
        Generate and add a specified number of movies to the database.
        :param db: The database dependency that provides access to the movie database.
        :param count: The number of movies to generate and add.
        :return: The list of generated movies.
        """
        # get the names of movies from the movie list and add a number to the end of each name
        movie_names = EntitiesRepo().get_movies_names(db)
        movies = []
        for i in range(2, count + 2):
            # generate a random movie name ensuring that the name is unique
            while True:
                new_movie_name = random.choice(movie_names)
                # if the new_movie_name does not have a number at the end, add 2 at the end
                if not new_movie_name[-1].isdigit():
                    new_movie_name += " 2"
                else:
                    # if the new_movie_name has a number at the end, increment the number by 1
                    new_movie_name = new_movie_name[:-1] + str(int(new_movie_name[-1]) + 1)

                if new_movie_name not in EntitiesRepo().get_movies_names(db):
                    break

            movie = MovieBase(name=new_movie_name,
                              year=random.randint(1950, 2022),
                              duration=f"{random.randint(1, 3)}h {random.randint(0, 59)}m",
                              genre=random.choice(
                                  ["Animation", "Adventure", "Comedy", "Action", "Drama", "Family", "Fantasy"]),
                              description=f"Generated Description for movie {new_movie_name} at {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

            EntitiesRepo().add_movie(db, movie)
            movies.append(movie)
        return movies

    @staticmethod
    def get_all_characters(db: db_dependency_characters):
        """
        Get all characters from the database.
        :param db: The database dependency that provides access to the character database.
        :return: A list of all characters.
        """
        characters = db.query(Character).all()
        return characters

    @staticmethod
    def get_characters_skip_limit(db: db_dependency_characters, skip: int, limit: int):
        """
        Get a specified number of characters from the database with pagination.
        :param db: The database dependency that provides access to the characters database.
        :param skip: The number of characters to skip before starting to return the characters.
        :param limit: The maximum number of characters to return.
        :return: A list of characters.
        """
        # characters = db.query(Character).offset(skip).limit(limit).all()
        characters = db.query(Character).order_by(Character.id).offset(skip).limit(limit).all()
        return characters

    @staticmethod
    def get_character(db: db_dependency_characters, character_id: int):
        """
        Get a character from the database by its id. If the character does not exist, return a 404 error.
        :param db: The database dependency that provides access to the characters database.
        :param character_id: The id of the character to get.
        :return: The character with the specified id.
        :raises HTTPException: If the character does not exist.
        """
        character = db.query(Character).filter(Character.id == character_id).first()
        if character is None:
            raise HTTPException(status_code=404, detail='Character not found')
        return character

    @staticmethod
    def add_character(db: db_dependency_characters, character: CharacterBase):
        """
        Add a new character to the database.
        :param db: The database dependency that provides access to the characters database.
        :param character: The character data to add to the database.
        :return: The newly added character.
        """
        new_db_character = Character(**character.dict())
        db.add(new_db_character)
        db.commit()
        db.refresh(new_db_character)
        return new_db_character

    @staticmethod
    def add_characters(db: db_dependency_characters, characters: List[CharacterBase]):
        """
        Add a list of new characters to the database.
        :param db: The database dependency that provides access to the characters database.
        :param characters: The list of character data to add to the database.
        :return: The list of added characters.
        """
        db_characters = [Character(**character.dict()) for character in characters]
        db.add_all(db_characters)
        db.commit()
        return db_characters

    @staticmethod
    def update_character(db: db_dependency_characters, character_id: int, character: CharacterBase):
        """
        Update a character in the database. If the character does not exist, return a 404 error.
        :param db: The database dependency that provides access to the character database.
        :param character_id: The id of the character to update.
        :param character: The new character data.
        :return: The updated character.
        :raises HTTPException: If the character does not exist.
        """
        db_character = db.query(Character).filter(Character.id == character_id).first()
        if db_character is None:
            raise HTTPException(status_code=404, detail='Character not found')
        for key, value in character.dict().items():
            if key != "editorId":
                setattr(db_character, key, value)
        db.commit()
        db.refresh(db_character)
        return db_character

    @staticmethod
    def delete_character(db: db_dependency_characters, character_id):
        """
        Delete a character from the database. If the character does not exist, return a 404 error.
        :param db: The database dependency that provides access to the character database.
        :param character_id: The id of the character to delete.
        :raises HTTPException: If the character does not exist.
        """
        db_character = db.query(Character).filter(Character.id == character_id).first()
        if db_character is None:
            raise HTTPException(status_code=404, detail='Character not found')
        db.delete(db_character)
        db.commit()

    @staticmethod
    def generate_and_add_characters(db: db_dependency_characters, count):
        """
        Generate and add characters to the character list
        :param db:
        :param count: Number of characters to generate
        :return: List of generated characters
        """
        movies_names = EntitiesRepo().get_movies_names(db)[:1000]
        # get the names of characters from the characters list and add a number to the end of each name
        for i in range(2, count + 2):
            newName = Faker().name()
            character = CharacterBase(name=newName,
                                      movieName=random.choice(movies_names),
                                      description=f"Generated Description for character {newName} at {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

            EntitiesRepo().add_character(db, character)
        return {"message": "Characters generated successfully"}

    @staticmethod
    def generate_characters_and_save_in_files(db: db_dependency_characters, count, file_name):
        """
        Generate characters and save them in a file
        :param db:
        :param count: Number of characters to generate
        :param file_name: Name of the file to save the characters.
        :return: None
        """

        movies_names = EntitiesRepo().get_movies_names(db)[:1000]
        with open(file_name, 'w', encoding="utf-8") as file:
            file.write('[')
            for i in range(2, count + 2):
                result = '{'
                result += f'"name": "{Faker().name()}",'
                result += f'"movieName": "{random.choice(movies_names)}",'
                result += f'"description": "Generated Description for character {Faker().name()} at {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}"'
                result += '},\n'
                file.write(result)
            file.write(']')

    @staticmethod
    def update_aggregated_column_movies(db_movies: db_dependency_movies, db_characters: db_dependency_characters):
        """
        Update the aggregated column in the movies table
        :param db_movies: Movies database
        :param db_characters: Characters database
        :return: None
        """
        # movies = EntitiesRepo().get_all_movies(db_movies)
        movies = EntitiesRepo().get_movies_skip_limit(db_movies, 0, 1000)
        for movie in movies:
            # Fetch all characters associated with the movie
            movie.nrCharacters = len(
                db_characters.query(Character).filter(Character.movieName == movie.name).all())
            # Commit the changes to the database
            db_movies.commit()
            db_movies.refresh(movie)

    @staticmethod
    def get_number_of_movies_in_database(db: db_dependency_movies):
        """
        Get the total number of movies in the database.
        :param db: The database dependency that provides access to the movies database.
        :return: The total number of movies in the database.
        """
        return db.query(Movie).count()

    @staticmethod
    def get_number_of_characters_in_database(db: db_dependency_characters):
        """
        Get the total number of characters in the database.
        :param db: The database dependency that provides access to the character database.
        :return: The total number of characters in the database.
        """
        return db.query(Character).count()

    @staticmethod
    def get_id_by_username(db: db_dependency_users, username: str):
        """
        Get the id of a user by their username. If the user does not exist, return None.
        :param db: The database dependency that provides access to the user's database.
        :param username: The username of the user.
        :return: The id of the user, or None if the user does not exist.
        """
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            return None
        return user.id

    @staticmethod
    def get_movies_by_userId(db: db_dependency_movies, user_id, skip: int, limit: int):
        """
        Get movies by a specific user id with pagination.
        :param db: The database dependency that provides access to the movies database.
        :param user_id: The id of the user.
        :param skip: The number of movies to skip before starting to return the movies.
        :param limit: The maximum number of movies to return.
        :return: A list of movies from the database. Each movie is represented as a MovieModel.
        """
        return db.query(Movie).filter(Movie.editorId == user_id).offset(skip).limit(limit).all()

    @staticmethod
    def get_characters_by_user(db: db_dependency_characters, username):
        """
        Get characters by a specific user.
        :param db: The database dependency that provides access to the characters database.
        :param username: The username of the user.
        :return: A list of characters from the database. Each character is represented as a CharacterModel.
        """
        user_id = EntitiesRepo().get_id_by_username(db, username)
        return db.query(Character).filter(Character.editorId == user_id).all()

    @staticmethod
    def login(db_users: db_dependency_users, username, password):
        """
        Authenticate a user with their username and password. If the username or password is incorrect, return a 401 error.
        :param db_users: The database dependency that provides access to the users database.
        :param username: The username of the user.
        :param password: The password of the user.
        :return: A dictionary containing the access token, the token type, and the id of the user.
        :raises HTTPException: If the username or password is incorrect.
        """
        user = db_users.query(User).filter(User.username == username).first()
        if user is None or not verify_password(password, user.hashedPassword):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return {"token": access_token, "token_type": "bearer", "user_id": user.id}

    @staticmethod
    def register(db: db_dependency_users, username, hashedPassword):
        """
        Register a new user. If a user with the same username already exists, return False.
        :param db: The database dependency that provides access to the users database.
        :param username: The username of the new user.
        :param hashedPassword: The hashed password of the new user.
        :return: True if the user was successfully registered, False otherwise.
        """
        if db.query(User).filter(User.username == username).first() is not None:
            return False
        new_user = User(username=username, hashedPassword=hashedPassword)
        db.add(new_user)
        db.commit()
        return True

    @staticmethod
    def verify_token(token):
        """
        Verify a token. If the token is invalid, return a 401 error.
        :param token: The token to verify.
        :return: A message indicating that the token is valid.
        :raises HTTPException: If the token is invalid.
        """
        payload = decode_access_token(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token - JWTError",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"message": "Token is valid"}

    @staticmethod
    def verify_admin_token(token):
        """
        Verify an admin token. If the token is invalid, return a 401 error.
        :param token: The token to verify.
        :return: A message indicating that the token is valid.
        :raises HTTPException: If the token is invalid.
        """
        payload = decode_access_token(token)
        if payload is None or payload.get("sub") != "admin":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token - JWTError",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"message": "Token is valid"}

    @staticmethod
    def update_aggregated_column_users(db):
        """
        Update the aggregated columns in the user's table.
        :param db: The database dependency that provides access to the user's database.
        :return: None
        """
        users = db.query(User).all()
        for user in users:
            user.nrMovies = len(db.query(Movie).filter(Movie.editorId == user.id).all())
            user.nrCharacters = len(db.query(Character).filter(Character.editorId == user.id).all())
            db.commit()
            db.refresh(user)

    @staticmethod
    def get_non_admin_users(db: db_dependency_users):
        """
        Get all non-admin users.
        :param db: The database dependency that provides access to the users database.
        :return: A list of all non-admin users.
        """
        EntitiesRepo().update_aggregated_column_users(db)

        return db.query(User).filter(User.username != 'admin').all()

    @staticmethod
    def remove_user_by_id(db: db_dependency_users, user_id):
        """
        Remove a user by their id. If the user does not exist, return a 404 error.
        :param db: The database dependency that provides access to the users database.
        :param user_id: The id of the user to remove.
        :return: A message indicating that the user was successfully deleted.
        :raises HTTPException: If the user does not exist.
        """
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=404, detail='User not found')
        db.delete(user)
        db.commit()
        return {"message": "User deleted successfully"}

    @staticmethod
    def get_user_by_id(db: db_dependency_users, user_id):
        """
        Get the details of a user by their id. If the user does not exist, return a 404 error.
        :param db: The database dependency that provides access to the users database.
        :param user_id: The id of the user to get.
        :return: The details of the user.
        :raises HTTPException: If the user does not exist.
        """
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=404, detail='User not found')
        return user
