import time
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from guesser.models import DailyPokemon, Pokemon
from guesser.views import GuessSerializer


class GuessSerializerTest(TestCase):
    """Test GuessSerializer validation logic."""

    def test_valid_guess(self):
        """Test serializer with valid input."""
        data = {"guess": "pikachu"}
        serializer = GuessSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["guess"], "pikachu")

    def test_valid_guess_with_whitespace(self):
        """Test serializer trims whitespace."""
        data = {"guess": "  Pikachu  "}
        serializer = GuessSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["guess"], "pikachu")

    def test_valid_guess_uppercase(self):
        """Test serializer converts to lowercase."""
        data = {"guess": "PIKACHU"}
        serializer = GuessSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["guess"], "pikachu")

    def test_missing_guess_field(self):
        """Test serializer rejects missing guess field."""
        data = {}
        serializer = GuessSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("guess", serializer.errors)

    def test_blank_guess(self):
        """Test serializer rejects blank guess."""
        data = {"guess": ""}
        serializer = GuessSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("guess", serializer.errors)

    def test_whitespace_only_guess(self):
        """Test serializer rejects whitespace-only guess."""
        data = {"guess": "   "}
        serializer = GuessSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("guess", serializer.errors)

    def test_guess_too_long(self):
        """Test serializer rejects guess exceeding max length."""
        data = {"guess": "a" * 101}  # Max is 100
        serializer = GuessSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("guess", serializer.errors)

    def test_guess_exactly_max_length(self):
        """Test serializer accepts guess at max length."""
        data = {"guess": "a" * 100}
        serializer = GuessSerializer(data=data)

        self.assertTrue(serializer.is_valid())


@pytest.mark.django_db
class QuestionViewTest(APITestCase):
    """Test QuestionView GET endpoint."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.url = "/api/v1/question"

        # Create test Pokemon
        self.pokemon = Pokemon.objects.create(
            id=1,
            number=25,
            name="Pikachu",
            sprite="pikachu.png",
            type1="Electric",
            type2="",
            live=True,
            mega=False,
            giga=False,
            generation=1,
        )

    def tearDown(self):
        """Clean up after tests."""
        cache.clear()

    @patch("guesser.views.GuesserService.get_todays_pokemon")
    def test_get_question_success(self, mock_get_pokemon: MagicMock):
        """Test successful retrieval of today's question."""
        daily_pokemon = DailyPokemon.objects.create(
            pokemon=self.pokemon.id, created=datetime.now(), date=datetime.now()
        )

        mock_get_pokemon.return_value = {
            "pokemon": self.pokemon,
            "daily_pokemon": daily_pokemon,
        }

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.pokemon.id)
        self.assertIn("date", response.data)
        mock_get_pokemon.assert_called_once()

    @patch("guesser.views.GuesserService.get_todays_pokemon")
    def test_get_question_not_found(self, mock_get_pokemon: MagicMock):
        """Test when no question is available."""
        mock_get_pokemon.return_value = None

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "No question available for today")

    @patch("guesser.views.GuesserService.get_todays_pokemon")
    def test_get_question_service_exception(self, mock_get_pokemon: MagicMock):
        """Test handling of service exceptions."""
        mock_get_pokemon.side_effect = Exception("Database error")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["error"], "Failed to get today's question")


@pytest.mark.django_db
class GuessViewTest(APITestCase):
    """Test GuessView POST endpoint with throttling."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.url = "/api/v1/guess"

        # Create test Pokemon
        self.correct_pokemon = Pokemon.objects.create(
            id=1,
            number=25,
            name="Pikachu",
            sprite="pikachu.png",
            type1="Electric",
            type2="",
            live=True,
            mega=False,
            giga=False,
            generation=1,
        )

        self.wrong_pokemon = Pokemon.objects.create(
            id=2,
            number=1,
            name="Bulbasaur",
            sprite="bulbasaur.png",
            type1="Grass",
            type2="Poison",
            live=True,
            mega=False,
            giga=False,
            generation=1,
        )

    def tearDown(self):
        """Clean up after tests."""
        cache.clear()

    @patch("guesser.views.GuesserService.get_todays_pokemon")
    @patch("guesser.views.GuesserService.check_guess")
    def test_correct_guess_first_attempt(
        self, mock_check_guess: MagicMock, mock_get_todays_pokemon: MagicMock
    ):
        """Test correct guess on first attempt."""
        mock_check_guess.return_value = {
            "correct": True,
            "guessed_pokemon": self.correct_pokemon,
            "hints": [],
        }

        mock_get_todays_pokemon.return_value = {
            "pokemon": self.correct_pokemon,
            "daily_pokemon": "",
        }

        response = self.client.post(self.url, {"guess": "pikachu"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["correct"])
        self.assertEqual(response.data["answer"]["name"], "Pikachu")
        self.assertEqual(response.data["attempt"], 1)

    @patch("guesser.views.GuesserService.check_guess")
    def test_incorrect_guess_first_attempt(self, mock_check_guess: MagicMock):
        """Test incorrect guess on first attempt returns hint."""
        mock_check_guess.return_value = {
            "correct": False,
            "guessed_pokemon": self.wrong_pokemon,
            "hints": ["Hint 1", "Hint 2"],
        }

        response = self.client.post(self.url, {"guess": "bulbasaur"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["correct"])
        self.assertEqual(response.data["attempt"], 1)
        self.assertEqual(response.data["attempts_remaining"], 2)
        self.assertEqual(response.data["hint"], "Hint 1")

    @patch("guesser.views.GuesserService.check_guess")
    def test_incorrect_guess_second_attempt(self, mock_check_guess: MagicMock):
        """Test incorrect guess on second attempt."""
        mock_check_guess.return_value = {
            "correct": False,
            "guessed_pokemon": self.wrong_pokemon,
            "hints": ["Hint 1", "Hint 2"],
        }

        # First attempt
        self.client.post(self.url, {"guess": "bulbasaur"})

        # Second attempt
        response = self.client.post(self.url, {"guess": "charmander"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["correct"])
        self.assertEqual(response.data["attempt"], 2)
        self.assertEqual(response.data["attempts_remaining"], 1)
        self.assertEqual(response.data["hint"], "Hint 2")

    @patch("guesser.views.GuesserService.check_guess")
    def test_incorrect_guess_third_attempt_shows_answer(
        self, mock_check_guess: MagicMock
    ):
        """Test third incorrect guess shows the answer."""
        mock_check_guess.return_value = {
            "correct": False,
            "guessed_pokemon": self.wrong_pokemon,
            "hints": ["Hint 1", "Hint 2"],
        }

        # Three attempts
        self.client.post(self.url, {"guess": "bulbasaur"})
        self.client.post(self.url, {"guess": "charmander"})
        response = self.client.post(self.url, {"guess": "squirtle"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["correct"])
        self.assertEqual(response.data["attempt"], 3)
        self.assertIn("answer", response.data)
        self.assertNotIn("hint", response.data)

    @patch("guesser.views.GuesserService.check_guess")
    def test_correct_guess_on_third_attempt(self, mock_check_guess: MagicMock):
        """Test correct guess on third attempt."""
        # First two attempts wrong
        mock_check_guess.return_value = {
            "correct": False,
            "guessed_pokemon": self.wrong_pokemon,
            "hints": ["Hint 1", "Hint 2"],
        }

        self.client.post(self.url, {"guess": "bulbasaur"})
        self.client.post(self.url, {"guess": "charmander"})

        # Third attempt correct
        mock_check_guess.return_value = {
            "correct": True,
            "guessed_pokemon": self.correct_pokemon,
            "hints": [],
        }

        response = self.client.post(self.url, {"guess": "pikachu"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["correct"])
        self.assertEqual(response.data["attempt"], 3)

    def test_throttle_blocks_fourth_request(self):
        """Test that fourth request is blocked by throttle."""
        with patch("guesser.views.GuesserService.check_guess") as mock_check:
            mock_check.return_value = {
                "correct": False,
                "guessed_pokemon": self.wrong_pokemon,
                "hints": ["Hint 1", "Hint 2"],
            }

            # Make 3 requests (should succeed)
            for _i in range(3):
                response = self.client.post(self.url, {"guess": "bulbasaur"})
                self.assertEqual(response.status_code, status.HTTP_200_OK)

            # Fourth request should be throttled
            response = self.client.post(self.url, {"guess": "pikachu"})
            self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_invalid_input_missing_guess(self):
        """Test request with missing guess field."""
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Invalid input")
        self.assertIn("details", response.data)

    def test_invalid_input_blank_guess(self):
        """Test request with blank guess."""
        response = self.client.post(self.url, {"guess": ""})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Invalid input")

    def test_invalid_input_whitespace_guess(self):
        """Test request with whitespace-only guess."""
        response = self.client.post(self.url, {"guess": "   "})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Invalid input")

    @patch("guesser.views.GuesserService.check_guess")
    def test_service_returns_none(self, mock_check_guess: MagicMock):
        """Test handling when service returns None."""
        mock_check_guess.return_value = None

        response = self.client.post(self.url, {"guess": "pikachu"})

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(
            response.data["error"], "An error occurred processing your guess"
        )

    @patch("guesser.views.GuesserService.check_guess")
    def test_service_raises_value_error(self, mock_check_guess: MagicMock):
        """Test handling of ValueError from service."""
        mock_check_guess.side_effect = ValueError("Invalid pokemon name")

        response = self.client.post(self.url, {"guess": "invalid"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Invalid Guess")

    @patch("guesser.views.GuesserService.check_guess")
    def test_service_raises_key_error(self, mock_check_guess: MagicMock):
        """Test handling of KeyError from service."""
        mock_check_guess.side_effect = KeyError("pokemon")

        response = self.client.post(self.url, {"guess": "pikachu"})

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(
            response.data["error"], "An error occurred processing your guess"
        )

    @patch("guesser.views.GuesserService.check_guess")
    def test_service_raises_generic_exception(self, mock_check_guess: MagicMock):
        """Test handling of generic exception from service."""
        mock_check_guess.side_effect = Exception("Database connection failed")

        response = self.client.post(self.url, {"guess": "pikachu"})

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(
            response.data["error"], "An error occurred processing your guess"
        )

    def test_guess_case_insensitive(self):
        """Test that guess is case-insensitive."""
        with patch("guesser.views.GuesserService.check_guess") as mock_check:
            mock_check.return_value = {
                "correct": True,
                "guessed_pokemon": self.correct_pokemon,
                "hints": [],
            }

            response = self.client.post(self.url, {"guess": "PIKACHU"})

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            # Verify the service received lowercase
            mock_check.assert_called_once_with("pikachu")

    def test_guess_whitespace_trimmed(self):
        """Test that whitespace is trimmed from guess."""
        with patch("guesser.views.GuesserService.check_guess") as mock_check:
            mock_check.return_value = {
                "correct": True,
                "guessed_pokemon": self.correct_pokemon,
                "hints": [],
            }

            response = self.client.post(self.url, {"guess": "  pikachu  "})

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            mock_check.assert_called_once_with("pikachu")


@pytest.mark.django_db
class ThrottleEnforcementTest(APITestCase):
    """Test throttle enforcement in detail."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.url = "/api/v1/guess"

        self.pokemon = Pokemon.objects.create(
            id=1,
            number=25,
            name="Pikachu",
            sprite="pikachu.png",
            type1="Electric",
            type2="",
            live=True,
            mega=False,
            giga=False,
            generation=1,
        )

    def tearDown(self):
        """Clean up after tests."""
        cache.clear()

    @patch("guesser.views.GuesserService.check_guess")
    def test_throttle_resets_daily(self, mock_check_guess: MagicMock):
        """Test that throttle resets at midnight."""
        mock_check_guess.return_value = {
            "correct": False,
            "guessed_pokemon": self.pokemon,
            "hints": ["Hint 1", "Hint 2"],
        }

        # Use up all 3 attempts
        for _i in range(3):
            response = self.client.post(self.url, {"guess": "bulbasaur"})
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Fourth should be throttled
        response = self.client.post(self.url, {"guess": "bulbasaur"})
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        # Clear cache to simulate next day
        cache.clear()

        # Should work again
        response = self.client.post(self.url, {"guess": "bulbasaur"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("guesser.views.GuesserService.check_guess")
    def test_throttle_per_ip_and_user_agent(self, mock_check_guess: MagicMock):
        """Test that throttle is per IP + User Agent combination."""
        mock_check_guess.return_value = {
            "correct": False,
            "guessed_pokemon": self.pokemon,
            "hints": ["Hint 1", "Hint 2"],
        }

        # Client 1 uses 3 attempts
        for _i in range(3):
            response = self.client.post(
                self.url,
                {"guess": "bulbasaur"},
                HTTP_USER_AGENT="Mozilla/5.0 Client1",
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Client 1 should be throttled
        response = self.client.post(
            self.url,
            {"guess": "bulbasaur"},
            HTTP_USER_AGENT="Mozilla/5.0 Client1",
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        # Client 2 with different user agent should still work
        response = self.client.post(
            self.url,
            {"guess": "bulbasaur"},
            HTTP_USER_AGENT="Mozilla/5.0 Client2",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("guesser.views.GuesserService.check_guess")
    def test_throttle_counter_increments_correctly(self, mock_check_guess: MagicMock):
        """Test that throttle counter increments correctly."""
        mock_check_guess.return_value = {
            "correct": False,
            "guessed_pokemon": self.pokemon,
            "hints": ["Hint 1", "Hint 2"],
        }

        # First request - attempt 1
        response = self.client.post(self.url, {"guess": "bulbasaur"})
        self.assertEqual(response.data["attempt"], 1)
        self.assertEqual(response.data["attempts_remaining"], 2)

        # Second request - attempt 2
        response = self.client.post(self.url, {"guess": "charmander"})
        self.assertEqual(response.data["attempt"], 2)
        self.assertEqual(response.data["attempts_remaining"], 1)

        # Third request - attempt 3
        response = self.client.post(self.url, {"guess": "squirtle"})
        self.assertEqual(response.data["attempt"], 3)


@pytest.mark.django_db
class RaceConditionTest(APITestCase):
    """Test race conditions and concurrent requests."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.url = "/api/v1/guess"

        self.pokemon = Pokemon.objects.create(
            id=1,
            number=25,
            name="Pikachu",
            sprite="pikachu.png",
            type1="Electric",
            type2="",
            live=True,
            mega=False,
            giga=False,
            generation=1,
        )

    def tearDown(self):
        """Clean up after tests."""
        cache.clear()

    @patch("guesser.views.GuesserService.check_guess")
    def test_sequential_requests_respect_throttle(self, mock_check_guess: MagicMock):
        """Test that sequential requests properly respect throttle."""
        mock_check_guess.return_value = {
            "correct": False,
            "guessed_pokemon": self.pokemon,
            "hints": ["Hint 1", "Hint 2"],
        }

        responses = []
        for i in range(5):
            response = self.client.post(
                self.url, {"guess": f"pokemon{i}"}, format="json"
            )
            responses.append(response)
            # Small delay to ensure sequential processing
            time.sleep(0.01)

        # First 3 should succeed
        self.assertEqual(responses[0].status_code, 200)
        self.assertEqual(responses[1].status_code, 200)
        self.assertEqual(responses[2].status_code, 200)

        # Last 2 should be throttled
        self.assertEqual(responses[3].status_code, 429)
        self.assertEqual(responses[4].status_code, 429)

    @patch("guesser.views.GuesserService.check_guess")
    def test_throttle_not_incremented_on_validation_error(
        self, mock_check_guess: MagicMock
    ):
        """Test that throttle counter doesn't increment on validation errors."""
        # First, make an invalid request
        response = self.client.post(self.url, {"guess": ""}, format="json")
        self.assertEqual(response.status_code, 400)

        # Now make valid requests - should still get 3 attempts
        mock_check_guess.return_value = {
            "correct": False,
            "guessed_pokemon": self.pokemon,
            "hints": ["Hint 1", "Hint 2"],
        }

        for i in range(3):
            response = self.client.post(self.url, {"guess": "bulbasaur"}, format="json")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data["attempt"], i + 1)

    @patch("guesser.views.GuesserService.check_guess")
    def test_multiple_validation_errors_dont_count(self, mock_check_guess: MagicMock):
        """Test that multiple validation errors don't increment throttle."""
        # Make 10 invalid requests
        for _i in range(10):
            response = self.client.post(self.url, {"guess": ""}, format="json")
            self.assertEqual(response.status_code, 400)

        # Should still have 3 attempts available
        mock_check_guess.return_value = {
            "correct": False,
            "guessed_pokemon": self.pokemon,
            "hints": ["Hint 1", "Hint 2"],
        }

        # First valid request should be attempt 1
        response = self.client.post(self.url, {"guess": "bulbasaur"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["attempt"], 1)


@pytest.mark.django_db
class EdgeCaseTest(APITestCase):
    """Test edge cases and boundary conditions."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.url = "/api/v1/guess"

        self.pokemon = Pokemon.objects.create(
            id=1,
            number=25,
            name="Pikachu",
            sprite="pikachu.png",
            type1="Electric",
            type2="",
            live=True,
            mega=False,
            giga=False,
            generation=1,
        )

    def tearDown(self):
        """Clean up after tests."""
        cache.clear()

    @patch("guesser.views.GuesserService.check_guess")
    def test_pokemon_with_no_type2(self, mock_check_guess: MagicMock):
        """Test Pokemon with only one type."""
        mock_check_guess.return_value = {
            "correct": True,
            "guessed_pokemon": self.pokemon,
            "hints": [],
        }

        response = self.client.post(self.url, {"guess": "pikachu"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["answer"]["type2"], "")

    @patch("guesser.views.GuesserService.check_guess")
    def test_pokemon_with_two_types(self, mock_check_guess: MagicMock):
        """Test Pokemon with two types."""
        dual_type_pokemon = Pokemon.objects.create(
            id=2,
            number=1,
            name="Bulbasaur",
            sprite="bulbasaur.png",
            type1="Grass",
            type2="Poison",
            live=True,
            mega=False,
            giga=False,
            generation=1,
        )

        mock_check_guess.return_value = {
            "correct": True,
            "guessed_pokemon": dual_type_pokemon,
            "hints": [],
        }

        response = self.client.post(self.url, {"guess": "bulbasaur"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["answer"]["type1"], "Grass")
        self.assertEqual(response.data["answer"]["type2"], "Poison")

    @patch("guesser.views.GuesserService.check_guess")
    def test_very_long_pokemon_name(self, mock_check_guess: MagicMock):
        """Test with maximum length pokemon name."""
        long_name = "a" * 100  # Max length

        mock_check_guess.return_value = {
            "correct": False,
            "guessed_pokemon": self.pokemon,
            "hints": ["Hint 1", "Hint 2"],
        }

        response = self.client.post(self.url, {"guess": long_name})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_check_guess.assert_called_once_with(long_name)

    @patch("guesser.views.GuesserService.check_guess")
    def test_special_characters_in_guess(self, mock_check_guess: MagicMock):
        """Test guess with special characters."""
        mock_check_guess.return_value = {
            "correct": False,
            "guessed_pokemon": self.pokemon,
            "hints": ["Hint 1", "Hint 2"],
        }

        response = self.client.post(self.url, {"guess": "mr-mime"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_check_guess.assert_called_once_with("mr-mime")

    @patch("guesser.views.GuesserService.check_guess")
    def test_unicode_in_guess(self, mock_check_guess: MagicMock):
        """Test guess with unicode characters."""
        mock_check_guess.return_value = {
            "correct": False,
            "guessed_pokemon": self.pokemon,
            "hints": ["Hint 1", "Hint 2"],
        }

        response = self.client.post(self.url, {"guess": "pikachū"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("guesser.views.GuesserService.check_guess")
    def test_request_with_additional_fields(self, mock_check_guess: MagicMock):
        """Test request with extra fields (should be ignored)."""
        mock_check_guess.return_value = {
            "correct": True,
            "guessed_pokemon": self.pokemon,
            "hints": [],
        }

        response = self.client.post(
            self.url,
            {"guess": "pikachu", "extra_field": "should_be_ignored"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
)
class CacheBackendTest(APITestCase):
    """Test with different cache backends."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.url = "/api/v1/guess"

        self.pokemon = Pokemon.objects.create(
            id=1,
            number=25,
            name="Pikachu",
            sprite="pikachu.png",
            type1="Electric",
            type2="",
            live=True,
            mega=False,
            giga=False,
            generation=1,
        )

    def tearDown(self):
        """Clean up after tests."""
        cache.clear()

    @patch("guesser.views.GuesserService.check_guess")
    def test_throttle_with_locmem_cache(self, mock_check_guess: MagicMock):
        """Test throttle works with local memory cache."""
        mock_check_guess.return_value = {
            "correct": False,
            "guessed_pokemon": self.pokemon,
            "hints": ["Hint 1", "Hint 2"],
        }

        # Make 3 requests
        for _i in range(3):
            response = self.client.post(self.url, {"guess": "bulbasaur"})
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Fourth should be throttled
        response = self.client.post(self.url, {"guess": "bulbasaur"})
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
