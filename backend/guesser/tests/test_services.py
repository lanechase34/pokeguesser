from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest

from guesser.models import DailyPokemon, Pokemon
from guesser.services import GuesserService, GuessResult, TodaysPokemonResult


# create_random_pokemon()
@pytest.mark.django_db  # allows access to Django database
class TestCreateRandomPokemon:
    def test_creates_daily_pokemon_for_today(self, live_pokemon: list[Pokemon]) -> None:
        result: DailyPokemon = GuesserService.create_random_pokemon()
        assert result is not None
        assert result.date == date.today()
        valid_ids: list[int] = [p.id for p in live_pokemon]
        assert result.pokemon in valid_ids

    def test_creates_daily_pokemon_for_specific_date(
        self, live_pokemon: list[Pokemon]
    ) -> None:
        target: date = date.today() - timedelta(days=5)
        result: DailyPokemon = GuesserService.create_random_pokemon(target_date=target)
        assert result is not None
        assert result.date == target
        valid_ids: list[int] = [p.id for p in live_pokemon]
        assert result.pokemon in valid_ids

    def test_returns_existing_daily_pokemon_if_already_created(
        self, today_pokemon: DailyPokemon
    ) -> None:
        """get_or_create should return the existing record, not create a new one"""

        # today_pokemon already created a pokemon for today
        # this call should not create a new entry
        result: DailyPokemon = GuesserService.create_random_pokemon(
            target_date=date.today()
        )
        assert result.pk == today_pokemon.pk
        # Only one row should exist for today
        assert DailyPokemon.objects.filter(date=date.today()).count() == 1

    @patch(
        "guesser.services.AuditService.log_error"
    )  # @patch() mocks - this creates a sub function
    @patch(
        "guesser.services.GuesserService._get_random_unused_pokemon_id",
        side_effect=Exception("DB exploded"),
    )  # this mocks that the exception DB Exploded is raised
    def test_logs_error_and_retries_fetch_on_exception(
        self,
        mock_get_random: MagicMock,
        mock_log_error: MagicMock,
        today_pokemon: DailyPokemon,
    ) -> None:
        """
        If get_or_create raises, we assume another thread created the row
        and fall back to a plain .get()
        """
        with patch(
            "django.db.models.QuerySet.get_or_create",
            side_effect=Exception("integrity error"),
        ):
            result: DailyPokemon = GuesserService.create_random_pokemon(
                target_date=date.today()
            )

        assert result.pk == today_pokemon.pk
        mock_log_error.assert_called_once()

    @patch(
        "django.db.models.QuerySet.get_or_create",
        side_effect=Exception("integrity error"),
    )
    @patch(
        "django.db.models.QuerySet.get",
        side_effect=DailyPokemon.DoesNotExist("gone"),
    )
    @patch("guesser.services.AuditService.log_error")
    def test_raises_if_fallback_get_also_fails(
        self,
        mock_log_error: MagicMock,
        mock_get: MagicMock,
        mock_get_or_create: MagicMock,
        live_pokemon: list[Pokemon],
    ) -> None:
        """If both get_or_create AND the fallback .get() fail, let it propagate"""
        with pytest.raises(DailyPokemon.DoesNotExist):
            GuesserService.create_random_pokemon(target_date=date.today())


# _get_random_unused_pokemon_id()
@pytest.mark.django_db
class TestGetRandomUnusedPokemonId:
    def test_returns_id_of_live_genderless_pokemon(
        self, live_pokemon: list[Pokemon]
    ) -> None:
        result: int = GuesserService._get_random_unused_pokemon_id()  # type: ignore[attr-defined] - ignore private function declaration
        valid_ids: list[int] = [p.id for p in live_pokemon]
        assert result in valid_ids

    def test_excludes_gendered_pokemon(
        self, live_pokemon: list[Pokemon], gendered_pokemon: Pokemon
    ) -> None:
        # Use up all live genderless pokemon
        for p in live_pokemon:
            DailyPokemon.objects.create(
                date=date.today() - timedelta(days=p.id), pokemon=p.id
            )

        # Only gendered_pokemon remains but it should be excluded
        with pytest.raises(Exception, match="All Pokemon have been selected"):
            GuesserService._get_random_unused_pokemon_id()  # type: ignore[attr-defined]

    def test_excludes_not_live_pokemon(
        self, live_pokemon: list[Pokemon], not_live_pokemon: Pokemon
    ) -> None:
        # Use up all live pokemon
        for p in live_pokemon:
            DailyPokemon.objects.create(
                date=date.today() - timedelta(days=p.id), pokemon=p.id
            )

        # Only not_live_pokemon remains but it should be excluded
        with pytest.raises(Exception, match="All Pokemon have been selected"):
            GuesserService._get_random_unused_pokemon_id()  # type: ignore[attr-defined]

    def test_excludes_already_used_pokemon(self, live_pokemon: list[Pokemon]) -> None:
        # Mark first 4 as used
        for p in live_pokemon[:4]:
            DailyPokemon.objects.create(
                date=date.today() - timedelta(days=p.id), pokemon=p.id
            )

        # Only live_pokemon[4] should be available
        result: int = GuesserService._get_random_unused_pokemon_id()  # type: ignore[attr-defined]
        assert result == live_pokemon[4].id

    @patch("guesser.services.AuditService.log_error")
    def test_raises_and_logs_when_no_pokemon_available(
        self, mock_log_error: MagicMock, live_pokemon: list[Pokemon]
    ) -> None:
        # Use up every pokemon
        for p in live_pokemon:
            DailyPokemon.objects.create(
                date=date.today() - timedelta(days=p.id), pokemon=p.id
            )

        with pytest.raises(Exception, match="All Pokemon have been selected"):
            GuesserService._get_random_unused_pokemon_id()  # type: ignore[attr-defined]

        mock_log_error.assert_called_once()
        assert "_GET_RANDOM_UNUSED_POKEMON_ID" in str(mock_log_error.call_args)

    def test_does_not_return_same_pokemon_twice_across_calls(
        self, live_pokemon: list[Pokemon]
    ) -> None:
        """
        Calling repeatedly should never return a
        pokemon that's already been assigned
        """
        selected_ids: list[int] = []
        for i in range(len(live_pokemon)):
            pokemon_id: int = GuesserService._get_random_unused_pokemon_id()  # type: ignore[attr-defined]
            assert pokemon_id not in selected_ids
            selected_ids.append(pokemon_id)
            # Simulate it being used
            DailyPokemon.objects.create(
                date=date.today() - timedelta(days=i + 1), pokemon=pokemon_id
            )


# get_todays_pokemon()
@pytest.mark.django_db
class TestGetTodaysPokemon:
    def test_returns_today_pokemon_and_pokemon(
        self, today_pokemon: DailyPokemon, live_pokemon: list[Pokemon]
    ) -> None:
        result: TodaysPokemonResult | None = GuesserService.get_todays_pokemon()
        assert result is not None
        assert result["daily_pokemon"].pk == today_pokemon.pk
        assert result["pokemon"].id == live_pokemon[0].id

    def test_accepts_custom_target_date(self, live_pokemon: list[Pokemon]) -> None:
        target: date = date.today() - timedelta(days=3)
        DailyPokemon.objects.create(date=target, pokemon=live_pokemon[1].id)
        result: TodaysPokemonResult | None = GuesserService.get_todays_pokemon(
            target_date=target
        )
        assert result is not None
        assert result["daily_pokemon"].date == target
        assert result["pokemon"].id == live_pokemon[1].id

    def test_lazy_creates_pokemon_if_none_exists(
        self, live_pokemon: list[Pokemon]
    ) -> None:
        """No DailyPokemon for today — should auto-create one"""
        assert DailyPokemon.objects.filter(date=date.today()).count() == 0
        result: TodaysPokemonResult | None = GuesserService.get_todays_pokemon()
        assert result is not None
        assert result["daily_pokemon"].date == date.today()
        assert DailyPokemon.objects.filter(date=date.today()).count() == 1

    @patch(
        "guesser.services.GuesserService.create_random_pokemon",
        side_effect=Exception("creation failed"),
    )
    def test_returns_none_if_lazy_creation_fails(
        self, mock_create: MagicMock, db: None
    ) -> None:
        result: TodaysPokemonResult | None = GuesserService.get_todays_pokemon()
        assert result is None

    @patch("guesser.services.AuditService.log_error")
    def test_returns_none_and_logs_if_pokemon_row_missing(
        self, mock_log_error: MagicMock, live_pokemon: list[Pokemon]
    ) -> None:
        """DailyPokemon exists but references a Pokemon ID that doesn't exist"""
        DailyPokemon.objects.create(date=date.today(), pokemon=9999)
        result: TodaysPokemonResult | None = GuesserService.get_todays_pokemon()
        assert result is None
        mock_log_error.assert_called_once()
        assert "GET_TODAYS_POKEMON" in str(mock_log_error.call_args)
        assert "9999" in str(mock_log_error.call_args)

    def test_defaults_target_date_to_today(
        self, today_pokemon: DailyPokemon, live_pokemon: list[Pokemon]
    ) -> None:
        """Passing None explicitly should behave the same as no argument"""
        result: TodaysPokemonResult | None = GuesserService.get_todays_pokemon(
            target_date=None
        )
        assert result is not None
        assert result["daily_pokemon"].date == date.today()

    def test_returns_cached_result_if_available(
        self, today_pokemon: DailyPokemon, live_pokemon: list[Pokemon]
    ) -> None:
        """Second call should return cached result without hitting the database"""

        # Prime the cache with a first call
        first_result: TodaysPokemonResult | None = GuesserService.get_todays_pokemon()
        assert first_result is not None

        # If cache is working, these should never be called
        with (
            patch("guesser.services.DailyPokemon.objects.get") as mock_daily_get,
            patch("guesser.services.Pokemon.objects.get") as mock_pokemon_get,
        ):
            second_result: TodaysPokemonResult | None = (
                GuesserService.get_todays_pokemon()
            )

            mock_daily_get.assert_not_called()
            mock_pokemon_get.assert_not_called()

        assert second_result is not None
        assert second_result["daily_pokemon"].pk == today_pokemon.pk
        assert second_result["pokemon"].id == live_pokemon[0].id


# check_guess()
@pytest.mark.django_db
class TestCheckGuess:
    def test_correct_guess_returns_true(
        self, today_pokemon: DailyPokemon, live_pokemon: list[Pokemon]
    ) -> None:
        result: GuessResult | None = GuesserService.check_guess(guess_name="Pokemon1")
        assert result is not None
        assert result["correct"] is True
        assert result["guessed_pokemon"] is not None
        assert result["guessed_pokemon"].id == live_pokemon[0].id

    def test_correct_guess_is_case_insensitive(
        self, today_pokemon: DailyPokemon, live_pokemon: list[Pokemon]
    ) -> None:
        result: GuessResult | None = GuesserService.check_guess(guess_name="pokemon1")
        assert result is not None
        assert result["correct"] is True

        result_upper: GuessResult | None = GuesserService.check_guess(
            guess_name="POKEMON1"
        )
        assert result_upper is not None
        assert result_upper["correct"] is True

    # MagicMock - fake above the 'patch' method each call with what arguments
    # (like createMock())
    @patch("guesser.services.AuditService.log")
    def test_logs_on_correct_guess(
        self,
        mock_log: MagicMock,
        today_pokemon: DailyPokemon,
        live_pokemon: list[Pokemon],
    ) -> None:
        GuesserService.check_guess(guess_name="Pokemon1")
        mock_log.assert_called()
        assert "CHECK_GUESS" in str(mock_log.call_args)

    def test_incorrect_guess_returns_false(
        self, today_pokemon: DailyPokemon, live_pokemon: list[Pokemon]
    ) -> None:
        result: GuessResult | None = GuesserService.check_guess(guess_name="Pokemon2")
        assert result is not None
        assert result["correct"] is False
        assert result["guessed_pokemon"] is not None
        assert result["guessed_pokemon"].id == live_pokemon[1].id

    @patch("guesser.services.AuditService.log")
    def test_does_not_log_on_incorrect_guess(
        self,
        mock_log: MagicMock,
        today_pokemon: DailyPokemon,
        live_pokemon: list[Pokemon],
    ) -> None:
        GuesserService.check_guess(guess_name="Pokemon2")
        mock_log.assert_not_called()

    def test_returns_false_with_none_pokemon_for_unknown_name(
        self, today_pokemon: DailyPokemon, live_pokemon: list[Pokemon]
    ) -> None:
        result: GuessResult | None = GuesserService.check_guess(guess_name="FakeMon")
        assert result is not None
        assert result["correct"] is False
        assert result["guessed_pokemon"] is None

    @patch("guesser.services.AuditService.log")
    @patch("guesser.services.Pokemon.objects.get")
    def test_returns_none_and_logs_warning_on_duplicate_pokemon(
        self,
        mock_pokemon_get: MagicMock,
        mock_log: MagicMock,
        today_pokemon: DailyPokemon,
        live_pokemon: list[Pokemon],
    ) -> None:
        # First call (in get_todays_pokemon) returns the real pokemon
        # Second call (in check_guess) raises MultipleObjectsReturned
        mock_pokemon_get.side_effect = [
            live_pokemon[0],  # First call succeeds
            Pokemon.MultipleObjectsReturned("dupe"),  # Second call raises
        ]

        result: GuessResult | None = GuesserService.check_guess(guess_name="Pokemon1")

        assert result is None
        mock_log.assert_called()
        assert "multiple" in str(mock_log.call_args).lower()

    @patch("guesser.services.GuesserService.get_todays_pokemon", return_value=None)
    @patch("guesser.services.AuditService.log_error")
    def test_returns_none_and_logs_if_no_todays_pokemon(
        self, mock_log_error: MagicMock, mock_get_today: MagicMock
    ) -> None:
        result: GuessResult | None = GuesserService.check_guess(guess_name="Pokemon1")
        assert result is None
        mock_log_error.assert_called_once()
        assert "CHECK_GUESS" in str(mock_log_error.call_args)

    def test_check_guess_with_custom_target_date(
        self, live_pokemon: list[Pokemon]
    ) -> None:
        target: date = date.today() - timedelta(days=2)
        DailyPokemon.objects.create(date=target, pokemon=live_pokemon[2].id)
        result: GuessResult | None = GuesserService.check_guess(
            guess_name="Pokemon3", target_date=target
        )
        assert result is not None
        assert result["correct"] is True

    def test_check_guess_defaults_target_date_to_today(
        self, today_pokemon: DailyPokemon, live_pokemon: list[Pokemon]
    ) -> None:
        result: GuessResult | None = GuesserService.check_guess(
            guess_name="Pokemon1", target_date=None
        )
        assert result is not None
        assert result["correct"] is True


# Race conditions
@pytest.mark.django_db(transaction=True)  # Uses real commits to database
class TestRaceConditions:
    def test_concurrent_create_random_pokemon_same_date(
        self, live_pokemon: list[Pokemon]
    ) -> None:
        """
        Fire off multiple threads all trying to create a DailyPokemon for
        the same date at the same time.
        Exactly one row should exist at the end and no unhandled
        exceptions should escape.
        """
        target: date = date.today() + timedelta(days=30)
        results: list[DailyPokemon] = []
        errors: list[Exception] = []

        def attempt() -> DailyPokemon | None:
            try:
                return GuesserService.create_random_pokemon(target_date=target)
            except Exception as e:
                errors.append(e)
                return None

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(attempt) for _ in range(10)]
            for future in as_completed(futures):
                result: DailyPokemon | None = future.result()
                if result:
                    results.append(result)

        # No unhandled errors
        assert len(errors) == 0, f"Unexpected errors: {errors}"

        # Exactly one row in the DB for that date
        assert DailyPokemon.objects.filter(date=target).count() == 1

        # All returned results point to the same row
        unique_pks: set[int] = {r.pk for r in results}
        assert len(unique_pks) == 1

    def test_concurrent_get_todays_pokemon_lazy_creation(
        self, live_pokemon: list[Pokemon]
    ) -> None:
        """
        Multiple threads call get_todays_pokemon simultaneously when no
        DailyPokemon exists yet
        The lazy-creation path should be safe
        only one row created, all threads get a valid result.
        """
        target: date = date.today() + timedelta(days=31)
        results: list[TodaysPokemonResult] = []
        errors: list[Exception] = []

        def attempt() -> TodaysPokemonResult | None:
            try:
                return GuesserService.get_todays_pokemon(target_date=target)
            except Exception as e:
                errors.append(e)
                return None

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(attempt) for _ in range(10)]
            for future in as_completed(futures):
                result: TodaysPokemonResult | None = future.result()
                if result:
                    results.append(result)

        assert len(errors) == 0, f"Unexpected errors: {errors}"
        assert DailyPokemon.objects.filter(date=target).count() == 1

        # Every thread that got a result should have the same pokemon
        pokemon_ids: set[int] = {r["pokemon"].id for r in results}
        assert len(pokemon_ids) == 1

    def test_concurrent_check_guess_does_not_corrupt(
        self, live_pokemon: list[Pokemon]
    ) -> None:
        """
        Hammer check_guess from many threads simultaneously.  Should never
        raise and results should be deterministic.
        """
        target: date = date.today() + timedelta(days=32)
        DailyPokemon.objects.create(date=target, pokemon=live_pokemon[0].id)

        results: list[GuessResult] = []
        errors: list[Exception] = []

        def attempt(name: str) -> GuessResult | None:
            try:
                return GuesserService.check_guess(guess_name=name, target_date=target)
            except Exception as e:
                errors.append(e)
                return None

        guesses: list[str] = ["Pokemon1", "Pokemon2", "FakeMon", "pokemon1", "POKEMON1"]

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(attempt, g) for g in guesses * 3]
            for future in as_completed(futures):
                result: GuessResult | None = future.result()
                if result:
                    results.append(result)

        assert len(errors) == 0, f"Unexpected errors: {errors}"

        # All results for "Pokemon1" (any casing) should be correct
        correct_results: list[GuessResult] = [
            r
            for r in results
            if r["guessed_pokemon"] is not None
            and r["guessed_pokemon"].name == "Pokemon1"
        ]
        assert all(r["correct"] is True for r in correct_results)

        # All results for "Pokemon2" should be incorrect
        wrong_results: list[GuessResult] = [
            r
            for r in results
            if r["guessed_pokemon"] is not None
            and r["guessed_pokemon"].name == "Pokemon2"
        ]
        assert all(r["correct"] is False for r in wrong_results)

        # All results for "FakeMon" should have guessed_pokemon as None
        fake_results: list[GuessResult] = [
            r for r in results if r["guessed_pokemon"] is None
        ]
        assert all(r["correct"] is False for r in fake_results)
