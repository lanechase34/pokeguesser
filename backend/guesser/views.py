import logging
from typing import Any, Dict, Never, Optional, cast

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import serializers, status
from rest_framework.exceptions import APIException
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from config.throttles import DailyRateThrottle

from .serializers import PokemonSerializer
from .services import GuesserService
from .utils import error_response, load_schema

logger = logging.getLogger(__name__)


class GuessSerializer(serializers.Serializer[Dict[str, Any]]):
    """
    Validates and normalizes a user's guess input.

    Strips whitespace and lowercases the value before validation.
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
    """
    Raised when a user exceeds the daily guess limit.

    Extends the default 429 response to include the correct answer,
    so the client can reveal it after the final attempt is exhausted.
    """

    status_code = status.HTTP_429_TOO_MANY_REQUESTS

    def __init__(self, answer: Any) -> None:
        self.detail: dict[str, Any] = {
            "correct": False,
            "answer": answer,
            "attempt": 3,
        }


class QuestionView(APIView):
    """Exposes today's Pokemon question."""

    @extend_schema(
        responses={
            200: OpenApiResponse(response=load_schema("question_get_200.json")),
            404: OpenApiResponse(
                response=error_response, description="No question available for today"
            ),
            500: OpenApiResponse(
                response=error_response, description="Unexpected server error"
            ),
        }
    )
    def get(self, request: Request, format: Optional[str] = None) -> Response:
        """
        Retrieve today's question.

        Returns the Pokemon ID and date for the current daily question.

        Returns:
            200: Today's question with ``id`` and ``date``.
            404: No question is available for today.
            500: An unexpected error occurred.
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
    """
    Accepts and evaluates guesses for today's Pokemon.

    Limited to 3 attempts per user per day via DailyRateThrottle.
    Each incorrect guess returns a progressively revealing hint.
    """

    throttle_classes = [DailyRateThrottle]
    throttle_scope = "guess_view"
    throttle_rate = 3

    def throttled(self, request: Request, wait: float) -> Never:
        """
        Override the default throttle handler to include today's answer.

        Reveals the correct answer in the 429 response body so the client
        can display it once the user has exhausted all attempts.

        Args:
            request: The incoming request that triggered the throttle.
            wait: Seconds remaining until the rate limit resets.

        Raises:
            ThrottledWithAnswer: Always; carries the serialized Pokemon answer.
        """
        result = GuesserService.get_todays_pokemon()
        if result is None:
            raise ThrottledWithAnswer(None)
        answer = PokemonSerializer(result["pokemon"]).data
        raise ThrottledWithAnswer(answer)

    @extend_schema(
        request=GuessSerializer,
        responses={
            200: OpenApiResponse(response=load_schema("guess_post_200.json")),
            400: OpenApiResponse(
                response=error_response, description="Invalid or missing guess"
            ),
            429: OpenApiResponse(response=load_schema("guess_post_429.json")),
            500: OpenApiResponse(
                response=error_response, description="Unexpected server error"
            ),
        },
    )
    def post(self, request: Request, format: Optional[str] = None) -> Response:
        """
        Submit a guess for today's Pokemon.

        Validates the guess, checks it against today's answer, and increments
        the attempt counter. Returns the answer on a correct guess or after the
        third attempt. Returns a hint on incorrect guesses with attempts remaining.

        Args:
            request: Must include a ``guess`` string in the request body.
            format: Optional response format suffix.

        Returns:
            200: Correct guess or final attempt - includes `correct`, `answer`,
                and `attempt`.
            200: Incorrect guess with attempts remaining - includes `correct`,
                `attempt`, `attempts_remaining`, and `hint`.
            400: Missing, blank, or otherwise invalid guess.
            500: An unexpected error occurred; attempt counter is rolled back.
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
