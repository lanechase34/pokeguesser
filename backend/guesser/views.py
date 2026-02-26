import logging
from typing import Any, Dict, Optional, cast

from rest_framework import serializers, status
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
                    "date": daily_question["daily_pokemon"].created,
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

        attempt = throttle.increment_counter(self)
        guess: str = serializer.validated_data["guess"]

        # Check the guess
        try:
            result = GuesserService.check_guess(guess)

            if result is None:
                raise KeyError("Today''s guess not found")

            answer = PokemonSerializer(result["guessed_pokemon"]).data

            # If correct or out of attempts
            if result["correct"] or attempt == 3:
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

        except (KeyError, Exception):
            logger.exception("Failed to check user's guess")
            return Response(
                {"error": "An error occurred processing your guess"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
