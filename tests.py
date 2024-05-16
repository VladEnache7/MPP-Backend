import unittest
from fastapi import FastAPI
from starlette.testclient import TestClient
from main import app
from typing import List
from schemas import MovieBase, MovieModel, CharacterModel, CharacterBase


class TestMoviesCRUD(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_get_movies(self):
        response = self.client.get("/movies")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), List)

    def test_add_movie(self):
        movie = MovieBase(name="Test Movie", year=2022, duration="2h", genre="Action", description="Test Description")
        response = self.client.post("/movies", json=movie.dict())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Test Movie")

    def test_get_movie(self):
        # First, add a movie
        movie = MovieBase(name="Test Movie", year=2022, duration="2h", genre="Action",
                          description="Test Description")
        response = self.client.post("/movies", json=movie.dict())
        self.assertEqual(response.status_code, 200)
        movie_id = response.json()["id"]

        # Then, get the movie using the id of the added movie
        response = self.client.get(f"/movies/{movie_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], movie_id)

    def test_update_movie(self):
        # First, add a movie
        movie = MovieBase(name="Test Movie", year=2022, duration="2h", genre="Action", description="Test Description")
        response = self.client.post("/movies", json=movie.dict())
        self.assertEqual(response.status_code, 200)
        movie_id = response.json()["id"]

        # Then, update the movie using the id of the added movie
        movie = MovieBase(name="Updated Movie", year=2022, duration="2h", genre="Action",
                          description="Updated Description")
        response = self.client.put(f"/movies/{movie_id}", json=movie.dict())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Updated Movie")

    def test_delete_movie(self):
        response = self.client.delete("/movies/4")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Movie deleted successfully")

    def test_get_characters(self):
        response = self.client.get("/characters")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), List)

    def test_add_character(self):
        character = CharacterBase(name="Test Character", movieName="Test Movie", description="Test Description")
        response = self.client.post("/characters", json=character.dict())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Test Character")

    def test_get_character(self):
        # First, add a character
        character = CharacterBase(name="Test Character", movieName="Test Movie", description="Test Description")
        response = self.client.post("/characters", json=character.dict())
        self.assertEqual(response.status_code, 200)
        character_id = response.json()["id"]

        # Then, get the character using the id of the added character
        response = self.client.get(f"/characters/{character_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], character_id)

    def test_update_character(self):
        # First, add a character
        character = CharacterBase(name="Test Character", movieName="Test Movie", description="Test Description")
        response = self.client.post("/characters", json=character.dict())
        self.assertEqual(response.status_code, 200)
        character_id = response.json()["id"]

        # Then, update the character using the id of the added character
        character = CharacterBase(name="Updated Character", movieName="Test Movie", description="Updated Description")
        response = self.client.put(f"/characters/{character_id}", json=character.dict())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Updated Character")

    def test_delete_character(self):
        response = self.client.delete("/characters/4")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Character deleted successfully")

    def test_add_bulk_characters(self):
        characters = [
            CharacterBase(name=f"Test Character {i}", movieName="Test Movie", description="Test Description")
            for i in range(5)]
        response = self.client.post("/characters/bulk/", json=[character.dict() for character in characters])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 5)


if __name__ == "__main__":
    unittest.main()
