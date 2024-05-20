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
            print(f"Data received by client: {data}")
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        active_connections.remove(websocket)


async def notify_clients():
    for connection in active_connections:
        message = {"message": "New data is available. Please refresh."}
        await connection.send_json(jsonable_encoder(message))

        print(f"Notified {len(active_connections)} clients with message: {message}")


# <todo> GET ALL movies from the database
@app.get('/movies', response_model=List[MovieModel])
async def get_movies(db: db_dependency_movies, skip: int = 0, limit: int = 50, token: str = Depends(oauth2_scheme)):
    EntitiesRepo().verify_token(token)
    movies = EntitiesRepo().get_movies_skip_limit(db, skip, limit)
    return movies


# <todo> GET ALL movies names from the database
@app.get('/movies/names', response_model=List[str])
async def get_movies_names(db: db_dependency_movies, token: str = Depends(oauth2_scheme)):
    EntitiesRepo().verify_token(token)
    movies_names = EntitiesRepo().get_movies_names(db)
    return movies_names


# <todo> GET a single movie from the database
@app.get('/movies/{movie_id}', response_model=MovieModel)
async def get_movie(db: db_dependency_movies, movie_id: int, token: str = Depends(oauth2_scheme)):
    EntitiesRepo().verify_token(token)
    movie = EntitiesRepo().get_movie(db, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail='Movie not found')
    return movie


# <todo> CREATE a new movie in the database
@app.post('/movies', response_model=MovieModel)
async def add_movie(db: db_dependency_movies, movie: MovieBase, token: str = Depends(oauth2_scheme)):
    EntitiesRepo().verify_token(token)
    added_movie = EntitiesRepo().add_movie(db, movie)
    await notify_clients()
    return added_movie


# <todo> UPDATE a movie in the database
@app.put('/movies/{movie_id}', response_model=MovieModel)
async def update_movie(db: db_dependency_movies, movie_id: int, movie: MovieBase, token: str = Depends(oauth2_scheme)):
    EntitiesRepo().verify_token(token)
    updated_movie = EntitiesRepo().update_movie(db, movie_id, movie)
    await notify_clients()
    return updated_movie


# <todo> DELETE a movie from the database
@app.delete('/movies/{movie_id}')
async def delete_movie(db: db_dependency_movies, movie_id: int, token: str = Depends(oauth2_scheme)):
    EntitiesRepo().delete_movie(db, movie_id)
    await notify_clients()
    return {'message': 'Movie deleted successfully'}


# <todo> DELETE a bulk of movies from the database
@app.delete('/movies/bulk/{movie_id_start}/{start_id}/{end_id}')
async def delete_bulk_movies(db: db_dependency_movies, start_id: int, end_id: int):
    deleted_movies = []
    not_found_movies = []
    for movie_id in range(start_id, end_id):
        try:
            EntitiesRepo().delete_movie(db, movie_id)
            deleted_movies.append(movie_id)
        except Exception as e:
            not_found_movies.append(movie_id)

    await notify_clients()
    return {'deleted': deleted_movies, 'not_found': not_found_movies}


# <todo> GET the number of movies in the database
@app.get('/movies/count/', response_model=dict)
async def get_movies_count(db: db_dependency_movies):
    movies_count = EntitiesRepo().get_number_of_movies_in_database(db)
    return {'count': movies_count}


# <todo> ADD a bulk of new movies at the same time in the database
@app.post('/movies/bulk/')
async def add_bulk_movies(db: db_dependency_movies, movies: List[MovieBase]):
    returned = EntitiesRepo().add_movies(db, movies)
    await notify_clients()
    return returned


# <todo> DELETE the duplicates from the database
@app.delete('/movies/delete_duplicates/')
async def delete_duplicates(db: db_dependency_movies):
    deleted_movies = EntitiesRepo().delete_duplicates(db)
    await notify_clients()
    return {'deleted_movies': deleted_movies}


generation_count = 0


async def generate_and_add_movies_periodically(db: db_dependency_movies, count):
    global generation_count
    EntitiesRepo().generate_and_add_movies(db, count)
    await notify_clients()
    print("Notified clients - main")
    generation_count += 1
    if generation_count < 5:
        # wait for 1 second before generating the next set of movies
        # time.sleep(1)
        # await generate_and_add_movies_periodically(db, count)
        threading.Timer(1, generate_and_add_movies_periodically, args=[count]).start()
        print(f"Generating {generation_count} time movies in background every 1 second")


# <todo> GENERATE n number of movies in the database periodically
@app.post('/movies/generate/{number}', response_model=dict)
async def generate_movies(db: db_dependency_movies, number: int, background_tasks: BackgroundTasks):
    global generation_count
    generation_count = 0
    # TODO: maybe here it will be an error with sending both parameters
    background_tasks.add_task(generate_and_add_movies_periodically, db, number)
    return {'message': f'Generating {number} movies in background every 1 seconds'}


# <todo> GET ALL characters from the database
@app.get('/characters', response_model=List[CharacterModel])
async def get_characters(db: db_dependency_characters, skip: int = 0, limit: int = 50,
                         token: str = Depends(oauth2_scheme)):
    EntitiesRepo().verify_token(token)
    characters = EntitiesRepo().get_characters_skip_limit(db, skip, limit)
    return characters


# <todo> GET a single character from the database
@app.get('/characters/{character_id}', response_model=CharacterModel)
async def get_character(db: db_dependency_characters, character_id: int, token: str = Depends(oauth2_scheme)):
    EntitiesRepo().verify_token(token)
    character = EntitiesRepo().get_character(db, character_id)
    if character is None:
        raise HTTPException(status_code=404, detail='Character not found')
    return character


# <todo> CREATE a new character in the database
@app.post('/characters', response_model=CharacterModel)
async def add_character(db_characters: db_dependency_characters, db_movies: db_dependency_movies,
                        character: CharacterBase, token: str = Depends(oauth2_scheme)):
    EntitiesRepo().verify_token(token)
    added_character = EntitiesRepo().add_character(db_characters, character)
    EntitiesRepo().update_aggregated_column_movies(db_movies, db_characters)
    await notify_clients()
    return added_character


# <todo> UPDATE a character in the database
@app.put('/characters/{character_id}', response_model=CharacterModel)
async def update_character(db: db_dependency_characters, character_id: int, character: CharacterBase,
                           token: str = Depends(oauth2_scheme)):
    updated_character = EntitiesRepo().update_character(db, character_id, character)
    await notify_clients()
    return updated_character


# <todo> DELETE a character from the database
@app.delete('/characters/{character_id}')
async def delete_character(db: db_dependency_characters, character_id: int, token: str = Depends(oauth2_scheme)):
    EntitiesRepo().verify_token(token)
    EntitiesRepo().delete_character(db, character_id)
    await notify_clients()
    return {'message': 'Character deleted successfully'}


# delete all the characters that are between 2 ids
@app.delete('/characters/bulk/{start_id}/{end_id}')
async def delete_bulk_characters(db: db_dependency_characters, start_id: int, end_id: int):
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


# <todo> ADD a bulk of new characters at the same time in the database
@app.post('/characters/bulk/', response_model=List[CharacterModel])
async def add_bulk_characters(db: db_dependency_characters, characters: List[CharacterBase]):
    added_characters = EntitiesRepo().add_characters(db, characters)
    await notify_clients()
    return added_characters


# <todo> UPDATE the aggregated column in the movies table
@app.put('/movies/update_nr_characters/')
async def update_nr_characters(db_movies: db_dependency_movies, db_characters: db_dependency_characters):
    try:
        EntitiesRepo().update_aggregated_column_movies(db_movies, db_characters)
        await notify_clients()
        return {'message': 'Aggregated column updated successfully'}
    except Exception as e:
        print(e)
        return {'message': 'Failed to update the aggregated column'}


# <todo> Get the number of characters in the database
@app.get('/characters/count/', response_model=dict)
async def get_characters_count(db: db_dependency_characters):
    characters_count = EntitiesRepo().get_number_of_characters_in_database(db)
    return {'count': characters_count}


# <todo> GENERATE n number of characters in the database
@app.post('/characters/generate/{number}', response_model=dict)
async def generate_characters(db: db_dependency_characters, number: int, token: str = Depends(oauth2_scheme)):
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


# <todo> login - verify user and password
@app.post('/auth/login/')
async def login(db_users: db_dependency_users, login_model: LoginRegisterModel):
    print(f'username: {login_model.username}, hashedPassword: {login_model.hashedPassword}')
    return EntitiesRepo().login(db_users, login_model.username, login_model.hashedPassword)


# <todo> register - add a new user
@app.post('/auth/register/', response_model=bool)
async def register(db: db_dependency_users, login_model: LoginRegisterModel):
    # Hash the password
    hashed_password = get_password_hash(login_model.hashedPassword)

    return EntitiesRepo().register(db, login_model.username, hashed_password)


# <todo> logout - remove the token from the database
@app.post('/auth/logout/')
async def logout(token: str = Depends(oauth2_scheme)):
    return EntitiesRepo().logout(token)


# TODO: add token verification for each api call
@app.get("/items/")
async def read_items(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    return {"token": payload}


# <todo> GET ALL characters for a specific username
@app.get('/characters/username/{username}', response_model=List[CharacterModel])
async def get_user(db_users: db_dependency_users, db_characters: db_dependency_characters, username: str,
                   token: str = Depends(oauth2_scheme)):
    EntitiesRepo().verify_token(token)
    userId = EntitiesRepo().get_id_by_username(db_users, username)
    if userId is None:
        raise HTTPException(status_code=404, detail='User not found')
    characters = EntitiesRepo().get_characters_by_user(db_characters, username)
    return characters


# <todo> GET ALL movies for a specific username
@app.get('/movies/username/{username}', response_model=List[MovieModel])
async def get_user_movies(db_users: db_dependency_users, db_movies: db_dependency_movies, username: str, skip: int = 0,
                          limit: int = 50, token: str = Depends(oauth2_scheme)):
    EntitiesRepo().verify_token(token)
    print(f'username: {username}')
    userId = EntitiesRepo().get_id_by_username(db_users, username)
    print(f'userId: {userId}')
    if userId is None:
        raise HTTPException(status_code=404, detail='User not found')
    movies = EntitiesRepo().get_movies_by_userId(db_movies, userId, skip, limit)
    return movies


# # <todo> GET ALL movies for a specific user id
# @app.get('/movies/userid/{userId}', response_model=List[MovieModel])
# async def get_user_movies_by_id(db_users: db_dependency_users, db_movies: db_dependency_movies, userId: int):
#     print(f'userId: {userId}')
#     movies = EntitiesRepo().get_movies_by_userId(db_movies, userId)
#     return movies


if __name__ == '__main__':
    # for Debugging purposes
    uvicorn.run(app, host="127.0.0.1", port=8000)
    pass
