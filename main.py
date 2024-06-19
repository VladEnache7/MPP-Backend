import threading
import time

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import List, Annotated
import models
from database import SessionLocalMovies, engine
from fastapi.middleware.cors import CORSMiddleware
from EntitiesRepository import EntitiesRepo
from schemas import MovieBase, MovieModel, CharacterModel, CharacterBase, LoginRegisterModel, TokenData
from fastapi.encoders import jsonable_encoder
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from auth_token import ALGORITHM, SECRET_KEY, get_password_hash, decode_access_token

# Create a new FastAPI instance
app = FastAPI()

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

active_connections: List[WebSocket] = []


def get_database():
    db = SessionLocalMovies()
    try:
        yield db
    finally:
        db.close()


db_dependency_movies = Annotated[models.Movie, Depends(get_database)]
db_dependency_characters = Annotated[models.Character, Depends(get_database)]
db_dependency_users = Annotated[models.User, Depends(get_database)]

models.Base_database.metadata.create_all(bind=engine)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@app.get("/", response_class=HTMLResponse)
async def read_item():
    return """
    <html>
        <head>
            <title>FastAPI WebSocket</title>
        </head>
        <body>
            <h1>WebSocket Server</h1>
            <p>WebSocket server is running successfully</p>
        </body>
    </html>
    """


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print("New client trying to connect")
    await websocket.accept()
    print("Client accepted")
    active_connections.append(websocket)
    print(f"Active connections: {len(active_connections)}")

    try:
        while True:
            data = await websocket.receive_text()
            # print(f"Data received by client: {data}")
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        active_connections.remove(websocket)


async def notify_clients():
    for connection in active_connections:
        message = {"message": "New data is available. Please refresh."}
        await connection.send_json(jsonable_encoder(message))
        print(f"Notified {len(active_connections)} clients with message: {message}")


@app.get('/movies', response_model=List[MovieModel])
async def get_movies(db: db_dependency_movies, skip: int = 0, limit: int = 50):
    """
        Retrieves a list of movies from the database.
        This function uses pagination to return a subset of movies. The number of movies to skip and the limit for the number of movies to return can be specified.

        :param db: The database dependency that provides access to the movies database.
        :param skip: The number of movies to skip.
        :param limit: The limit for the number of movies to return.
        :return: A list of movies from the database.
        :raises: HTTPException: If
        """
    return EntitiesRepo().get_movies_skip_limit(db, skip, limit)


@app.get('/movies/names', response_model=List[str])
async def get_movies_names(db: db_dependency_movies, token: str = Depends(oauth2_scheme)):
    """
    Retrieves a list of movie names from the database.
    This function verifies the provided token and then uses the EntitiesRepo().get_movies_names() method to retrieve the movie names from the database.

    :param db: The database dependency that provides access to the movie database.
    :param token: The token to verify the user's authentication.
    :return: A list of movie names from the database.
    :raises: HTTPException: If the token verification fails.
    """
    EntitiesRepo().verify_token(token)
    return EntitiesRepo().get_movies_names(db)


@app.get('/movies/{movie_id}', response_model=MovieModel)
async def get_movie(db: db_dependency_movies, movie_id: int, token: str = Depends(oauth2_scheme)):
    """
        Retrieves a specific movie from the database using its ID.

        :param db: The database dependency that provides access to the movies database.
        :param movie_id: The ID of the movie to retrieve.
        :param token: The token to verify the user's authentication.
        :return: The movie with the specified ID.
        :raises: HTTPException: If the movie is not found in the database or the token verification fails.
        """
    EntitiesRepo().verify_token(token)
    movie = EntitiesRepo().get_movie(db, movie_id)
    return movie


@app.post('/movies', response_model=MovieModel)
async def add_movie(db: db_dependency_movies, movie: MovieBase, token: str = Depends(oauth2_scheme)):
    """
    Adds a new movie to the database.

    :param db: The database dependency that provides access to the movies' database.
    :param movie: The movie data to add.
    :param token: The token to verify the user's authentication.
    :return: The added movie.
    :raises: HTTPException: If the token verification fails.
    """
    EntitiesRepo().verify_token(token)
    added_movie = EntitiesRepo().add_movie(db, movie)
    await notify_clients()
    return added_movie


@app.put('/movies/{movie_id}', response_model=MovieModel)
async def update_movie(db: db_dependency_movies, movie_id: int, movie: MovieBase, token: str = Depends(oauth2_scheme)):
    """
    Updates a specific movie in the database using its ID.

    :param db: The database dependency that provides access to the movies' database. \
    :param movie_id: The ID of the movie to update.
    :param movie: The updated movie data.
    :param token: The token to verify the user's authentication.
    :return: The updated movie.
    :raises: HTTPException: If the movie is not found in the database or the token verification fails.
    """
    EntitiesRepo().verify_token(token)
    updated_movie = EntitiesRepo().update_movie(db, movie_id, movie)
    await notify_clients()
    return updated_movie


@app.delete('/movies/{movie_id}')
async def delete_movie_by_id(db: db_dependency_movies, movie_id: int, token: str = Depends(oauth2_scheme)):
    """
    Delete a movie from the database by its id. If the movie does not exist, return a 404 error.
    :param db: The database dependency that provides access to the movie database.
    :param movie_id: The id of the movie to delete.
    :return: A message indicating that the movie was successfully deleted.
    :raises HTTPException: If the movie does not exist.
    """
    EntitiesRepo().delete_movie_by_id(db, movie_id)
    await notify_clients()
    return {'message': 'Movie deleted successfully'}


@app.delete('/movies/by_name/{movie_name}')
async def delete_movie_by_name(db: db_dependency_movies, movie_name: str, token: str = Depends(oauth2_scheme)):
    """
    Delete a movie from the database by its name. If the movie does not exist, return a 404 error.
    :param db: The database dependency that provides access to the movie database.
    :param movie_name: The id of the movie to delete.
    :return: A message indicating that the movie was successfully deleted.
    :raises HTTPException: If the movie does not exist.
    """
    EntitiesRepo().delete_movie_by_name(db, movie_name)
    await notify_clients()
    return {'message': 'Movie deleted successfully'}


@app.delete('/movies/bulk/{movie_id_start}/{start_id}/{end_id}')
async def delete_bulk_movies(db: db_dependency_movies, start_id: int, end_id: int):
    """
    Delete a range of movies from the database. If a movie does not exist, it is skipped.
    :param db: The database dependency that provides access to the movies database.
    :param start_id: The id of the first movie to delete.
    :param end_id: The id of the last movie to delete.
    :return: A dictionary containing the ids of the deleted movies and the ids of the movies that were not found.
    """
    deleted_movies, not_found_movies = [], []
    for movie_id in range(start_id, end_id):
        try:
            EntitiesRepo().delete_movie_by_id(db, movie_id)
            deleted_movies.append(movie_id)
        except HTTPException as e:
            not_found_movies.append(movie_id)

    await notify_clients()
    return {'deleted': deleted_movies, 'not_found': not_found_movies}


@app.get('/movies/count/', response_model=dict)
async def get_movies_count(db: db_dependency_movies):
    """
    Get the total number of movies in the database.
    :param db: The database dependency that provides access to the movies database.
    :return: A dictionary containing the total number of movies in the database.
    """
    movies_count = EntitiesRepo().get_number_of_movies_in_database(db)
    return {'count': movies_count}


@app.post('/movies/bulk/')
async def add_bulk_movies(db: db_dependency_movies, movies: List[MovieBase]):
    """
    Add a list of new movies to the database.
    If a movie with the same name already exists, it is skipped.
    :param db: The database dependency that provides access to the movie database.
    :param movies: The list of movie data to add to the database.
    :return: The list of added movies.
    """
    returned = EntitiesRepo().add_movies(db, movies)
    await notify_clients()
    return returned


# TODO: This may not be necessary anymore
@app.delete('/movies/delete_duplicates/')
async def delete_duplicates(db: db_dependency_movies):
    """
    Delete duplicate movies from the database.
    :param db: The database dependency that provides access to the movies database.
    :return: A dictionary containing the deleted movies.
    """
    deleted_movies = EntitiesRepo().delete_duplicates(db)
    await notify_clients()
    return {'deleted_movies': deleted_movies}


generation_count = 0


# TODO: Also this may not be necessary anymore since all the movies need to be real right now
async def generate_and_add_movies_periodically(db: db_dependency_movies, count):
    """
    Generate and add a specified number of movies to the database periodically.
    :param db: The database dependency that provides access to the movies database.
    :param count: The number of movies to generate and add.
    :return: None
    """
    global generation_count
    EntitiesRepo().generate_and_add_movies(db, count)
    await notify_clients()
    print("Notified clients - main")
    generation_count += 1
    if generation_count < 5:
        threading.Timer(1, generate_and_add_movies_periodically, args=[count]).start()
        print(f"Generating {generation_count} time movies in background every 1 second")


@app.post('/movies/generate/{number}', response_model=dict)
async def generate_movies(db: db_dependency_movies, number: int, background_tasks: BackgroundTasks):
    """
    Generate and add a specified number of movies to the database.
    :param db: The database dependency that provides access to the movies database.
    :param number: The number of movies to generate and add.
    :return: A message indicating that the movies are being generated.
    """
    global generation_count
    generation_count = 0
    # TODO: maybe here it will be an error with sending both parameters
    background_tasks.add_task(generate_and_add_movies_periodically, db, number)
    return {'message': f'Generating {number} movies in background every 1 seconds'}


@app.get('/characters', response_model=List[CharacterModel])
async def get_characters(db: db_dependency_characters, skip: int = 0, limit: int = 50,
                         token: str = Depends(oauth2_scheme)):
    """
    Get a specified number of characters from the database with pagination.
    :param db: The database dependency that provides access to the characters database.
    :param skip: The number of characters to skip before starting to return the characters.
    :param limit: The maximum number of characters to return.
    :return: A list of characters.
    """
    EntitiesRepo().verify_token(token)
    characters = EntitiesRepo().get_characters_skip_limit(db, skip, limit)
    return characters


@app.get('/characters/{character_id}', response_model=CharacterModel)
async def get_character(db: db_dependency_characters, character_id: int, token: str = Depends(oauth2_scheme)):
    """
    Get a character from the database by its id. If the character does not exist, return a 404 error.
    :param db: The database dependency that provides access to the characters database.
    :param character_id: The id of the character to get.
    :return: The character with the specified id.
    :raises HTTPException: If the character does not exist.
    """
    EntitiesRepo().verify_token(token)
    character = EntitiesRepo().get_character(db, character_id)
    if character is None:
        raise HTTPException(status_code=404, detail='Character not found')
    return character


@app.post('/characters', response_model=CharacterModel)
async def add_character(db_characters: db_dependency_characters, db_movies: db_dependency_movies,
                        character: CharacterBase, token: str = Depends(oauth2_scheme)):
    """
    Add a new character to the database.
    :param db_characters: The database dependency that provides access to the characters database.
    :param db_movies: The database dependency that provides access to the movies database.
    :param character: The character data to add to the database.
    :return: The newly added character.
    """
    EntitiesRepo().verify_token(token)
    added_character = EntitiesRepo().add_character(db_characters, character)
    EntitiesRepo().update_aggregated_column_movies(db_movies, db_characters)
    await notify_clients()
    return added_character


@app.put('/characters/{character_id}', response_model=CharacterModel)
async def update_character(db: db_dependency_characters, character_id: int, character: CharacterBase,
                           token: str = Depends(oauth2_scheme)):
    """
    Update a character in the database. If the character does not exist, return a 404 error.
    :param db: The database dependency that provides access to the characters database.
    :param character_id: The id of the character to update.
    :param character: The new character data.
    :return: The updated character.
    :raises HTTPException: If the character does not exist.
    """
    updated_character = EntitiesRepo().update_character(db, character_id, character)
    await notify_clients()
    return updated_character


@app.delete('/characters/{character_id}')
async def delete_character(db: db_dependency_characters, character_id: int, token: str = Depends(oauth2_scheme)):
    """
    Delete a character from the database. If the character does not exist, return a 404 error.
    :param db: The database dependency that provides access to the characters database.
    :param character_id: The id of the character to delete.
    :return: A message indicating that the character was successfully deleted.
    :raises HTTPException: If the character does not exist.
    """
    EntitiesRepo().verify_token(token)
    EntitiesRepo().delete_character(db, character_id)
    await notify_clients()
    return {'message': 'Character deleted successfully'}


@app.delete('/characters/bulk/{start_id}/{end_id}')
async def delete_bulk_characters(db: db_dependency_characters, start_id: int, end_id: int):
    """
    Delete a range of characters from the database. If a character does not exist, it is skipped.
    :param db: The database dependency that provides access to the characters database.
    :param start_id: The id of the first character to delete.
    :param end_id: The id of the last character to delete.
    :return: A dictionary containing the ids of the deleted characters and the ids of the characters that were not found.
    """
    deleted_characters = []
    not_found_characters = []
    for character_id in range(start_id, end_id):
        try:
            EntitiesRepo().delete_character(db, character_id)
            deleted_characters.append(character_id)
        except Exception as e:
            not_found_characters.append(character_id)
    await notify_clients()
    return {'deleted': deleted_characters, 'not_found': not_found_characters}


@app.post('/characters/bulk/', response_model=List[CharacterModel])
async def add_bulk_characters(db: db_dependency_characters, characters: List[CharacterBase]):
    """
    Add a list of new characters to the database.
    :param db: The database dependency that provides access to the characters database.
    :param characters: The list of character data to add to the database.
    :return: The list of added characters.
    """
    added_characters = EntitiesRepo().add_characters(db, characters)
    await notify_clients()
    return added_characters


@app.put('/movies/update_nr_characters/')
async def update_nr_characters(db_movies: db_dependency_movies, db_characters: db_dependency_characters):
    """
    Update the number of characters in each movie in the database.
    :param db_movies: The database dependency that provides access to the movies database.
    :param db_characters: The database dependency that provides access to the characters database.
    :return: A message indicating whether the update was successful.
    """
    try:
        EntitiesRepo().update_aggregated_column_movies(db_movies, db_characters)
        await notify_clients()
        return {'message': 'Aggregated column updated successfully'}
    except Exception as e:
        print(e)
        return {'message': 'Failed to update the aggregated column'}


@app.get('/characters/count/', response_model=dict)
async def get_characters_count(db: db_dependency_characters):
    """
    Get the total number of characters in the database.
    :param db: The database dependency that provides access to the characters database.
    :return: A dictionary containing the total number of characters in the database.
    """
    characters_count = EntitiesRepo().get_number_of_characters_in_database(db)
    return {'count': characters_count}


@app.post('/characters/generate/{number}', response_model=dict)
async def generate_characters(db: db_dependency_characters, number: int, token: str = Depends(oauth2_scheme)):
    """
    Generate a specified number of characters and save them in files.
    :param db: The database dependency that provides access to the characters database.
    :param number: The number of characters to generate.
    :param token: The token to verify.
    :return: A message indicating that the characters were generated.
    :raises HTTPException: If the token is invalid.
    """
    EntitiesRepo().verify_token(token)
    threads = []
    for i in range(10):
        file_name = f'characters_{i}.json'
        thread = threading.Thread(target=EntitiesRepo().generate_characters_and_save_in_files,
                                  args=(db, number, file_name))
        threads.append(thread)
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    return {'message': f'Generated {number} characters'}


@app.post('/auth/login/')
async def login(db_users: db_dependency_users, login_model: LoginRegisterModel):
    """
    Authenticate a user with their username and password. If the username or password is incorrect, return a 401 error.
    :param db_users: The database dependency that provides access to the users database.
    :param login_model: The login data of the user.
    :return: A dictionary containing the access token, the token type, and the id of the user.
    :raises HTTPException: If the username or password is incorrect.
    """
    print(f'username: {login_model.username}, hashedPassword: {login_model.hashedPassword}')
    return EntitiesRepo().login(db_users, login_model.username, login_model.hashedPassword)


@app.post('/auth/register/', response_model=bool)
async def register(db: db_dependency_users, login_model: LoginRegisterModel):
    """
    Register a new user. If a user with the same username already exists, return False.
    :param db: The database dependency that provides access to the users database.
    :param login_model: The registration data of the new user.
    :return: True if the user was successfully registered, False otherwise.
    """
    # Hash the password
    hashed_password = get_password_hash(login_model.hashedPassword)
    return EntitiesRepo().register(db, login_model.username, hashed_password)


# TODO: Not sure this should be here
@app.get("/items/")
async def read_items(token: str = Depends(oauth2_scheme)):
    """
    Decode a token.
    :param token: The token to decode.
    :return: The decoded token.
    """
    payload = decode_access_token(token)
    return {"token": payload}


@app.get('/characters/username/{username}', response_model=List[CharacterModel])
async def get_user_characters(db_users: db_dependency_users, db_characters: db_dependency_characters, username: str,
                              token: str = Depends(oauth2_scheme)):
    """
    Get a user's characters from the database. If the user does not exist, return a 404 error.
    :param db_users: The database dependency that provides access to the user's database.
    :param db_characters: The database dependency that provides access to the character database.
    :param username: The username of the user.
    :param token: The token to verify.
    :return: A list of the user's characters.
    :raises HTTPException: If the user does not exist or the token is invalid.
    """
    EntitiesRepo().verify_token(token)
    userId = EntitiesRepo().get_id_by_username(db_users, username)
    if userId is None:
        raise HTTPException(status_code=404, detail='User not found')
    characters = EntitiesRepo().get_characters_by_user(db_characters, username)
    return characters


@app.get('/movies/username/{username}', response_model=List[MovieModel])
async def get_user_movies(db_users: db_dependency_users, db_movies: db_dependency_movies, username: str, skip: int = 0,
                          limit: int = 50, token: str = Depends(oauth2_scheme)):
    """
    Get a user's movies from the database. If the user does not exist, return a 404 error.
    :param db_users: The database dependency that provides access to the user's database.
    :param db_movies: The database dependency that provides access to the movie database.
    :param username: The username of the user.
    :param skip: The number of movies to skip before starting to return the movies.
    :param limit: The maximum number of movies to return.
    :param token: The token to verify.
    :return: A list of the user's movies.
    :raises HTTPException: If the user does not exist or the token is invalid.
    """
    EntitiesRepo().verify_token(token)
    print(f'username: {username}')
    userId = EntitiesRepo().get_id_by_username(db_users, username)
    print(f'userId: {userId}')
    if userId is None:
        raise HTTPException(status_code=404, detail='User not found')
    movies = EntitiesRepo().get_movies_by_userId(db_movies, userId, skip, limit)
    return movies


@app.get('/users/basicUsers/')
async def get_basic_users(db_users: db_dependency_users, token: str = Depends(oauth2_scheme)):
    """
    Get all basic users.
    :param db_users: The database dependency that provides access to the user's database.
    :param token: The token to verify that is a valid user.
    :return: A list of all basic users.
    :raises HTTPException: If the token is invalid.
    """
    EntitiesRepo().verify_token(token)
    users = EntitiesRepo().get_basic_users(db_users)
    return users


@app.get('/users/nonAdmin/')
async def get_non_admin_users(db_users: db_dependency_users, token: str = Depends(oauth2_scheme)):
    """
    Get all non-admin users.
    :param db_users: The database dependency that provides access to the user's database.
    :param token: The token to verify that the user is an admin.
    :return: A list of all non-admin users.
    :raises HTTPException: If the token is invalid.
    """
    EntitiesRepo().verify_admin_token(token)
    users = EntitiesRepo().get_non_admin_users(db_users)
    return users


@app.delete('/users/{userId}')
async def remove_user_by_id(db_users: db_dependency_users, userId: int, token: str = Depends(oauth2_scheme)):
    """
    Remove a user by their id. If the user does not exist, return a 404 error.
    :param db_users: The database dependency that provides access to the user's database.
    :param userId: The id of the user to remove.
    :param token: The token to verify that the user is an admin.
    :return: A message indicating that the user was successfully removed.
    :raises HTTPException: If the user does not exist or the token is invalid.
    """
    EntitiesRepo().verify_admin_token(token)
    return EntitiesRepo().remove_user_by_id(db_users, userId)


@app.get('/users/userId/{userId}')
async def get_user_by_id(db_users: db_dependency_users, userId: int, token: str = Depends(oauth2_scheme)):
    """
    Get a user by their id. If the user does not exist, return a 404 error.
    :param db_users: The database dependency that provides access to the user's database.
    :param userId: The id of the user to get.
    :param token: The token to verify the user.
    :return: The user with the specified id.
    :raises HTTPException: If the user does not exist or the token is invalid.
    """
    EntitiesRepo().verify_token(token)
    user = EntitiesRepo().get_user_by_id(db_users, userId)
    if user is None:
        raise HTTPException(status_code=404, detail='User not found')
    return user


@app.get('/moviesTMDB/')
async def fetch_movies_from_tmdb():
    """
    Fetch movies from The Movie Database (TMDB) API.
    """
    return EntitiesRepo().fetch_movies_from_tmdb()["results"]


if __name__ == '__main__':
    # for Debugging purposes
    uvicorn.run(app, host="127.0.0.1", port=8000)
    pass
