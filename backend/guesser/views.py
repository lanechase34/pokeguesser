import logging
from typing import Any, Dict, Never, Optional, cast

from rest_framework import serializers, status
from rest_framework.exceptions import APIException
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from config.throttles import DailyRateThrottle

from .serializers import PokemonSerializer
from .services import GuesserService

logger = logging.getLogger(__name__)


class GuessSerializer(serializers.Serializer[Dict[str, Any]]):
    """
    Serialize to validate guess user input
    """

    guess = serializers.CharField(
        max_length=100, required=True, trim_whitespace=True, allow_blank=False
    )

    def validate_guess(self, value: str) -> str:
        value = value.strip().lower()
        if not value:
            raise serializers.ValidationError("Guess not provided")
        return value


class ThrottledWithAnswer(APIException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS

    def __init__(self, answer: Any) -> None:
        self.detail: dict[str, Any] = {
            "correct": False,
            "answer": answer,
            "attempt": 3,
        }


class QuestionView(APIView):
    def get(self, request: Request, format: Optional[str] = None) -> Response:
        """
        GET to retrieve today's question
        """

        try:
            daily_question = GuesserService.get_todays_pokemon()

            if not daily_question:
                return Response(
                    {"error": "No question available for today"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            return Response(
                {
                    "id": daily_question["pokemon"].id,
                    "date": daily_question["daily_pokemon"].date,
                },
                status=status.HTTP_200_OK,
            )

        except Exception:
            logger.exception("Failed to get today's question")
            return Response(
                {"error": "Failed to get today's question"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GuessView(APIView):
    throttle_classes = [DailyRateThrottle]
    throttle_scope = "guess_view"
    throttle_rate = 3

    def throttled(self, request: Request, wait: float) -> Never:
        """Override to return the answer alongside the 429"""
        result = GuesserService.get_todays_pokemon()
        if result is None:
            raise ThrottledWithAnswer(None)
        answer = PokemonSerializer(result["pokemon"]).data
        raise ThrottledWithAnswer(answer)

    def post(self, request: Request, format: Optional[str] = None) -> Response:
        """
        POST to submit a user's guess for today's pokemon
        Max 3 attempts per day, each failed attempt gives a new hint
        """

        throttle = cast(DailyRateThrottle, self.get_throttles()[0])

        # Validate input
        serializer = GuessSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "Invalid input", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        guess: str = serializer.validated_data["guess"]

        # Check the guess
        incremented = False
        try:
            result = GuesserService.check_guess(guess)

            if result is None:
                raise KeyError("Today's guess not found")

            attempt = throttle.increment_counter(self)
            incremented = True

            # If correct or out of attempts
            if result["correct"] or attempt == 3:
                todays_pokemon = GuesserService.get_todays_pokemon()
                if todays_pokemon is None:
                    raise KeyError("Today's pokemon not found")
                answer = PokemonSerializer(todays_pokemon["pokemon"]).data
                return Response(
                    {
                        "correct": result["correct"],
                        "answer": answer,
                        "attempt": attempt,
                    },
                    status=status.HTTP_200_OK,
                )

            # If incorrect, provide the a hint based on current attempt
            return Response(
                {
                    "correct": False,
                    "attempt": attempt,
                    "attempts_remaining": 3 - attempt,
                    "hint": result["hints"][attempt - 1],
                },
                status=status.HTTP_200_OK,
            )
        except ValueError:
            return Response(
                {"error": "Invalid Guess"}, status=status.HTTP_400_BAD_REQUEST
            )

        except Exception:
            # Don't increment counter on server error
            if incremented:
                throttle.decrement_counter(self)

            logger.exception("Failed to check user's guess")
            return Response(
                {"error": "An error occurred processing your guess"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
