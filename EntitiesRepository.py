import random
from datetime import datetime, timedelta
from typing import Annotated, List
from faker import Faker
from fastapi import Depends, HTTPException
from starlette import status

import models
from database import SessionLocalMovies
from schemas import MovieBase, CharacterBase
from auth_token import create_access_token, verify_password, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES


def get_database():
    db = SessionLocalMovies()
    try:
        yield db
    finally:
        db.close()


db_dependency_movies = Annotated[models.Movie, Depends(get_database)]
db_dependency_characters = Annotated[models.Character, Depends(get_database)]
db_dependency_users = Annotated[models.User, Depends(get_database)]


class EntitiesRepo:

    @staticmethod
    def get_all_movies(db: db_dependency_movies):
        movies = db.query(models.Movie).all()
        return movies

    @staticmethod
    def get_movies_names(db: db_dependency_movies):
        movies = db.query(models.Movie).all()
        return [movie.name for movie in movies]

    @staticmethod
    def get_movies_skip_limit(db: db_dependency_movies, skip: int, limit: int):
        # TODO Expected type 'Session', got 'Type[Movie]' instead
        movies = db.query(models.Movie).offset(skip).limit(limit).all()
        # movies = db.query(models.Movie).order_by(models.Movie.id).offset(skip).limit(limit).all()
        return movies

    @staticmethod
    def get_movie(db: db_dependency_movies, movie_id: int):
        movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
        if movie is None:
            raise HTTPException(status_code=404, detail='Movie not found')
        return movie

    @staticmethod
    def add_movie(db: db_dependency_movies, movie: MovieBase):
        new_db_movie = models.Movie(**movie.dict())
        if db.query(models.Movie).filter(models.Movie.name == movie.name).first() is not None:
            raise HTTPException(status_code=400, detail='Movie already exists')
        db.add(new_db_movie)
        db.commit()
        db.refresh(new_db_movie)
        return new_db_movie

    @staticmethod
    def add_movies(db: db_dependency_movies, movies: List[MovieBase]):
        db_movies = [models.Movie(**movie.dict()) for movie in movies]
        # added_movies = []
        # not_added_movies = []
        for movie in db_movies:
            # find if exists a movie with this name
            if db.query(models.Movie).filter(models.Movie.name == movie.name).first() is not None:
                # not_added_movies.append(movie)
                continue
            # added_movies.append(movie)
            db.add(movie)
            db.commit()
        db.commit()

        return {"added_movies": 1, "not_added_movies": 2}

    @staticmethod
    def update_movie(db: db_dependency_movies, movie_id: int, movie: MovieBase):
        db_movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
        if db_movie is None:
            raise HTTPException(status_code=404, detail='Movie not found')
        for key, value in movie.dict().items():
            setattr(db_movie, key, value)
        db.commit()
        db.refresh(db_movie)
        return db_movie

    @staticmethod
    def delete_movie(db: db_dependency_movies, movie_id):
        db_movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
        if db_movie is None:
            raise HTTPException(status_code=404, detail='Movie not found')
        db.delete(db_movie)
        db.commit()

    # delete duplicates from the movies list
    @staticmethod
    def delete_duplicates(db: db_dependency_movies):
        deleted_movies = []
        movies = db.query(models.Movie).all()
        movie_names = [movie.name for movie in movies]
        for movie in movies:
            if movie_names.count(movie.name) > 1:
                deleted_movies.append(movie)
                db.delete(movie)
                movie_names.remove(movie.name)
        db.commit()
        return deleted_movies

    @staticmethod
    def generate_and_add_movies(db: db_dependency_movies, count):
        """
        Generate and add movies to the movies list
        :param db:
        :param count: Number of movies to generate
        :return: List of generated movies
        """

        # get the names of movies from the movies list and add a number to the end of each name
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
        characters = db.query(models.Character).all()
        return characters

    @staticmethod
    def get_characters_skip_limit(db: db_dependency_characters, skip: int, limit: int):
        # characters = db.query(models.Character).offset(skip).limit(limit).all()
        characters = db.query(models.Character).order_by(models.Character.id).offset(skip).limit(limit).all()
        return characters

    @staticmethod
    def get_character(db: db_dependency_characters, character_id: int):
        character = db.query(models.Character).filter(models.Character.id == character_id).first()
        if character is None:
            raise HTTPException(status_code=404, detail='Character not found')
        return character

    @staticmethod
    def add_character(db: db_dependency_characters, character: CharacterBase):
        new_db_character = models.Character(**character.dict())
        db.add(new_db_character)
        db.commit()
        db.refresh(new_db_character)
        return new_db_character

    @staticmethod
    def add_characters(db: db_dependency_characters, characters: List[CharacterBase]):
        db_characters = [models.Character(**character.dict()) for character in characters]
        db.add_all(db_characters)
        db.commit()
        return db_characters

    @staticmethod
    def update_character(db: db_dependency_characters, character_id: int, character: CharacterBase):
        db_character = db.query(models.Character).filter(models.Character.id == character_id).first()
        if db_character is None:
            raise HTTPException(status_code=404, detail='Character not found')
        for key, value in character.dict().items():
            setattr(db_character, key, value)
        db.commit()
        db.refresh(db_character)
        return db_character

    @staticmethod
    def delete_character(db: db_dependency_characters, character_id):
        db_character = db.query(models.Character).filter(models.Character.id == character_id).first()
        if db_character is None:
            raise HTTPException(status_code=404, detail='Character not found')
        db.delete(db_character)
        db.commit()

    @staticmethod
    def generate_and_add_characters(db: db_dependency_characters, count):
        """
        Generate and add characters to the characters list
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
        :param file_name: Name of the file to save the characters
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
        # Fetch all movies
        # movies = EntitiesRepo().get_all_movies(db_movies)
        movies = EntitiesRepo().get_movies_skip_limit(db_movies, 0, 1000)

        for movie in movies:
            # Fetch all characters associated with the movie
            movie.nrCharacters = len(
                db_characters.query(models.Character).filter(models.Character.movieName == movie.name).all())

            # Commit the changes to the database
            db_movies.commit()
            db_movies.refresh(movie)

    @staticmethod
    def get_number_of_movies_in_database(db: db_dependency_movies):
        # get the highest id from the movies table

        return db.query(models.Movie).count()

    @staticmethod
    def get_number_of_characters_in_database(db: db_dependency_characters):
        return db.query(models.Character).count()

    @staticmethod
    def get_id_of_user(db: db_dependency_users, username):
        user = db.query(models.User).filter(models.User.username == username).first()
        if user is None:
            return None
        return user.id

    @staticmethod
    def get_movies_by_user(db: db_dependency_movies, username):
        user_id = EntitiesRepo().get_id_of_user(db, username)
        return db.query(models.Movie).filter(models.Movie.editorId == user_id).all()

    @staticmethod
    def get_characters_by_user(db: db_dependency_characters, username):
        user_id = EntitiesRepo().get_id_of_user(db, username)
        return db.query(models.Character).filter(models.Character.editorId == user_id).all()

    @staticmethod
    def login(db: db_dependency_users, username, password):
        user = db.query(models.User).filter(models.User.username == username).first()
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
        return {"access_token": access_token, "token_type": "bearer"}

    @staticmethod
    def register(db: db_dependency_users, username, hashedPassword):
        if db.query(models.User).filter(models.User.username == username).first() is not None:
            return False
        new_user = models.User(username=username, hashedPassword=hashedPassword)
        db.add(new_user)
        db.commit()
        return True


if __name__ == '__main__':
    print(EntitiesRepo().get_all_movies())
