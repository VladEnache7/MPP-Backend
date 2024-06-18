import unittest
from fastapi import FastAPI
from starlette.testclient import TestClient
from main import app
from typing import List
from schemas import MovieBase, MovieModel, CharacterModel, CharacterBase


class TestMoviesCRUD(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    # <----------------------------> Movies Tests <---------------------------->
    def test_get_movies(self):
        response = self.client.get("/movies")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), List)

    def test_add_movie(self):
        # Login and get the token
        response = self.client.post("/auth/login/", json={"username": "test", "hashedPassword": "test"})
        token = response.json().get('token')

        # Create a new movie
        movie = MovieBase(name="Test Movie", year=2022, duration="2h", genre="Action", description="Test Description")

        # Include the token in the header of your post request
        response = self.client.post("/movies", headers={"Authorization": f"Bearer {token}"}, json=movie.dict())

        self.assertEqual(response.status_code, 200)

        # Test the response
        self.assertEqual(response.json()["name"], "Test Movie")
        self.assertEqual(response.json()["year"], 2022)
        self.assertEqual(response.json()["duration"], "2h")
        self.assertEqual(response.json()["genre"], "Action")
        self.assertEqual(response.json()["description"], "Test Description")

        # delete the movie after the test
        response = self.client.delete(f"/movies/{response.json()['id']}",
                                      headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 200)

    def test_get_movie(self):
        # Login and get the token
        response = self.client.post("/auth/login/", json={"username": "test", "hashedPassword": "test"})
        token = response.json().get('token')

        # First, add a movie
        movie = MovieBase(name="Test Movie", year=2022, duration="2h", genre="Action",
                          description="Test Description")
        response = self.client.post("/movies", headers={"Authorization": f"Bearer {token}"}, json=movie.dict())
        self.assertEqual(response.status_code, 200)
        movie_id = response.json()["id"]

        # Then, get the movie using the id of the added movie
        response = self.client.get(f"/movies/{movie_id}", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], movie_id)

        # delete the movie after the test
        response = self.client.delete(f"/movies/{response.json()['id']}", headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 200)

    def test_update_movie(self):
        # Login and get the token
        response = self.client.post("/auth/login/", json={"username": "test", "hashedPassword": "test"})
        token = response.json().get('token')

        # First, add a movie
        movie = MovieBase(name="Test Movie", year=2022, duration="2h", genre="Action", description="Test Description")
        response = self.client.post("/movies", headers={"Authorization": f"Bearer {token}"}, json=movie.dict())
        self.assertEqual(response.status_code, 200)
        movie_id = response.json()["id"]

        # Then, update the movie using the id of the added movie
        movie = MovieBase(name="Updated Movie", year=2022, duration="2h", genre="Action",
                          description="Updated Description")
        response = self.client.put(f"/movies/{movie_id}", headers={"Authorization": f"Bearer {token}"},
                                   json=movie.dict())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Updated Movie")

        # delete the movie after the test
        response = self.client.delete(f"/movies/{response.json()['id']}", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 200)

    def test_delete_movie(self):
        # Login and get the token
        response = self.client.post("/auth/login/", json={"username": "test", "hashedPassword": "test"})
        token = response.json().get('token')

        # First, add a movie
        movie = MovieBase(name="Test Movie", year=2022, duration="2h", genre="Action", description="Test Description")
        response = self.client.post("/movies", headers={"Authorization": f"Bearer {token}"}, json=movie.dict())
        self.assertEqual(response.status_code, 200)
        movie_id = response.json()["id"]

        # Then, delete the movie using the id of the added movie
        response = self.client.delete(f"/movies/{movie_id}", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 200)

    def test_add_bulk_movies(self):
        # Login and get the token
        response = self.client.post("/auth/login/", json={"username": "test", "hashedPassword": "test"})
        token = response.json().get('token')

        movies = [
            MovieBase(name=f"Test Movie {i}", year=2022, duration="2h", genre="Action", description="Test Description")
            for i in range(5)]
        response = self.client.post("/movies/bulk/", headers={"Authorization": f"Bearer {token}"},
                                    json=[movie.dict() for movie in movies])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(len(response.json()['added_movies']) + len(response.json()['not_added_movies']), 5)

        # delete the movies after the test by their names
        for movie in movies:
            response = self.client.delete(f"/movies/by_name/{movie.name}", headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(response.status_code, 200)

    # <----------------------------> Characters Tests <---------------------------->
    def test_get_characters(self):
        # Login and get the token
        response = self.client.post("/auth/login/", json={"username": "test", "hashedPassword": "test"})
        token = response.json().get('token')

        # Get the characters
        response = self.client.get("/characters", headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 200)

    def test_add_character(self):
        # Login and get the token
        response = self.client.post("/auth/login/", json={"username": "test", "hashedPassword": "test"})
        token = response.json().get('token')

        # Create a new character
        character = CharacterBase(name="Test Character", movieName="Test Movie", description="Test Description")

        # Include the token in the header of your post request
        response = self.client.post("/characters", headers={"Authorization": f"Bearer {token}"}, json=character.dict())

        self.assertEqual(response.status_code, 200)

        # Test the response
        self.assertEqual(response.json()["name"], "Test Character")
        self.assertEqual(response.json()["movieName"], "Test Movie")
        self.assertEqual(response.json()["description"], "Test Description")

        # delete the character after the test
        response = self.client.delete(f"/characters/{response.json()['id']}",
                                      headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 200)

    def test_get_character(self):
        # Login and get the token
        response = self.client.post("/auth/login/", json={"username": "test", "hashedPassword": "test"})
        token = response.json().get('token')

        # First, add a character
        character = CharacterBase(name="Test Character", movieName="Test Movie", description="Test Description")
        response = self.client.post("/characters", headers={"Authorization": f"Bearer {token}"}, json=character.dict())
        self.assertEqual(response.status_code, 200)
        character_id = response.json()["id"]

        # Then, get the character using the id of the added character
        response = self.client.get(f"/characters/{character_id}", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], character_id)

        # delete the character after the test
        response = self.client.delete(f"/characters/{response.json()['id']}",
                                      headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 200)

    def test_update_character(self):
        # Login and get the token
        response = self.client.post("/auth/login/", json={"username": "test", "hashedPassword": "test"})
        token = response.json().get('token')

        # First, add a character
        character = CharacterBase(name="Test Character", movieName="Test Movie", description="Test Description")
        response = self.client.post("/characters", headers={"Authorization": f"Bearer {token}"}, json=character.dict())
        self.assertEqual(response.status_code, 200)
        character_id = response.json()["id"]

        # Then, update the character using the id of the added character
        character = CharacterBase(name="Updated Character", movieName="Test Movie", description="Updated Description")
        response = self.client.put(f"/characters/{character_id}", headers={"Authorization": f"Bearer {token}"},
                                   json=character.dict())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Updated Character")

        # delete the character after the test
        response = self.client.delete(f"/characters/{response.json()['id']}",
                                      headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 200)

    def test_delete_character(self):
        # Login and get the token
        response = self.client.post("/auth/login/", json={"username": "test", "hashedPassword": "test"})
        token = response.json().get('token')

        # First, add a character
        character = CharacterBase(name="Test Character", movieName="Test Movie", description="Test Description")
        response = self.client.post("/characters", headers={"Authorization": f"Bearer {token}"}, json=character.dict())
        self.assertEqual(response.status_code, 200)
        character_id = response.json()["id"]

        # Then, delete the character using the id of the added character
        response = self.client.delete(f"/characters/{character_id}", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 200)

    def test_add_bulk_characters(self):
        # Login and get the token
        response = self.client.post("/auth/login/", json={"username": "test", "hashedPassword": "test"})
        token = response.json().get('token')

        characters = [
            CharacterBase(name=f"Test Character {i}", movieName="Test Movie", description="Test Description")
            for i in range(5)]
        response = self.client.post("/characters/bulk/", headers={"Authorization": f"Bearer {token}"},
                                    json=[character.dict() for character in characters])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 5)

        # delete the characters after the test
        for character in response.json():
            response = self.client.delete(f"/characters/{character['id']}",
                                          headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(response.status_code, 200)

    # <----------------------------> Users Tests <---------------------------->


if __name__ == "__main__":
    unittest.main()
