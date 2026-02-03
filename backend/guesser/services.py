from __future__ import annotations
from django.db.models import OuterRef, Exists
from datetime import date
from django.db import transaction
from .models import Pokemon, DailyPokemon
from audit.services import AuditService
from typing import TypedDict


class TodaysPokemonResult(TypedDict):
    daily_pokemon: DailyPokemon
    pokemon: Pokemon


class GuessResult(TypedDict):
    correct: bool
    guessed_pokemon: Pokemon | None


class GuesserService:
    @staticmethod  # function does not require 'self' argument
    @transaction.atomic  # all or nothing
    def create_random_pokemon(
        target_date: date | None = None, triggered_by: str = "system"
    ) -> DailyPokemon:
        """
        Select a random Pokemon that hasn't been chosen yet for the given date
        Thread-safe: uses get_or_create to prevent duplicate creation.

        Args:
            target_date: Date to select pokemon for (defaults to today)
            triggered_by: What triggered the event

        Returns:
            DailyPokemon instance
        """

        # So this is weird, but this is because date.today() would only be evaluated once if it were in the function args
        if target_date is None:
            target_date = date.today()

        # Check if pokemon already exists for this date
        try:
            # get_or_create handles all locking internally
            daily_pokemon, created = DailyPokemon.objects.get_or_create(
                date=target_date,
                defaults={"pokemon": GuesserService._get_random_unused_pokemon_id()},
            )

            if created:
                AuditService.log(
                    app_name="guesser",
                    event_type="CREATE_RANDOM_POKEMON",
                    message=f"Created new pokemon {daily_pokemon.pokemon} for {target_date}",
                    triggered_by=triggered_by,
                )
            return daily_pokemon
        except Exception as e:
            AuditService.log_error(
                app_name="guesser",
                event_type="CREATE_RANDOM_POKEMON",
                message=f"Failed to create pokemon for {target_date}",
                exception=e,
                triggered_by=triggered_by,
            )
            # If this failed, another thread probably created it
            # Try fetch again
            return DailyPokemon.objects.get(date=target_date)

    @staticmethod
    def _get_random_unused_pokemon_id() -> int:
        """
        Private function
        Get a random unused Pokemon ID

        Returns:
            PK of random usused pokemon
        """

        # Subquery to check if Pokemon exists in DailyPokemon
        used_pokemon_subquery = DailyPokemon.objects.filter(pokemon=OuterRef("id"))

        # Get Pokemon that have not been selected (similar to LEFT OUTER JOIN WHERE NULL)
        available_pokemon = Pokemon.objects.annotate(
            has_been_used=Exists(used_pokemon_subquery)
        ).filter(
            has_been_used=False,
            live=True,  # only select live pokemon
            gender="",  # avoid gender-specific species
        )

        # Select a random pokemon
        random_pokemon: Pokemon | None = available_pokemon.order_by("?").first()

        if random_pokemon is None:
            # TO-DO Reset here
            AuditService.log_error(
                app_name="guesser",
                event_type="_GET_RANDOM_UNUSED_POKEMON_ID",
                message="All Pokemon have been selected!",
            )
            raise Exception("All Pokemon have been selected!")

        return random_pokemon.id

    @staticmethod
    def get_todays_pokemon(
        target_date: date | None = None,
    ) -> TodaysPokemonResult | None:
        """
        Get today's Pokemon with all data
        Lazy loads - if no pokemon exists (nightly job failed), create one, then return it

        Args:
            target_date: Date to select pokemon for (defaults to today)

        Returns:
            TodaysPokemonResult with 'daily_pokemon' and 'pokemon' keys, or None on failure
        """

        if target_date is None:
            target_date = date.today()

        # Select DailyPokemon based on today's date
        try:
            daily_pokemon: DailyPokemon = DailyPokemon.objects.get(date=target_date)
        except DailyPokemon.DoesNotExist:
            # Create if doesn't exist
            try:
                daily_pokemon: DailyPokemon = GuesserService.create_random_pokemon(
                    target_date=target_date
                )
            except Exception:
                return None

        # Fetch the Pokemon data from POGO Tracker
        try:
            pokemon = Pokemon.objects.get(id=daily_pokemon.pokemon)
        except Pokemon.DoesNotExist:
            AuditService.log_error(
                app_name="guesser",
                event_type="GET_TODAYS_POKEMON",
                message=f"DailyPokemon references non-existent Pokemon ID {daily_pokemon.pokemon}",
            )
            return None

        return {"daily_pokemon": daily_pokemon, "pokemon": pokemon}

    @staticmethod
    def check_guess(
        guess_name: str, target_date: date | None = None
    ) -> GuessResult | None:
        """
        Check if the guess matches today's pokemon.

        Args:
            guess_name: Name of the pokemon the user guessed
            target_date: Date to check against (defaults to today)

        Returns:
            dict with 'correct' bool and 'guessed_pokemon' Pokemon instance,
            or None if the guess or daily pokemon is invalid
        """
        if target_date is None:
            target_date = date.today()

        # Get today's pokemon
        today = GuesserService.get_todays_pokemon(target_date=target_date)
        if today is None:
            AuditService.log_error(
                app_name="guesser",
                event_type="CHECK_GUESS",
                message=f"Could not fetch today's pokemon for {target_date}",
            )
            return None

        result: GuessResult = {"correct": False, "guessed_pokemon": None}
        # Look up the guessed pokemon by name (case-insensitive)
        try:
            guessed_pokemon = Pokemon.objects.get(name__iexact=guess_name)
        except Pokemon.DoesNotExist:
            return result
        except Pokemon.MultipleObjectsReturned:
            # Just in case multiple pokemon were created with same name
            AuditService.log(
                app_name="guesser",
                event_type="CHECK_GUESS",
                message=f"Guess '{guess_name}' matched multiple pokemon",
                level="WARNING",
            )
            return None

        result["correct"] = guessed_pokemon.id == today["daily_pokemon"].pokemon
        result["guessed_pokemon"] = guessed_pokemon

        if result["correct"]:
            AuditService.log(
                app_name="guesser",
                event_type="CHECK_GUESS",
                message=f"Guess '{guess_name}' was correct for {target_date}!",
                level="INFO",
            )

        return result
