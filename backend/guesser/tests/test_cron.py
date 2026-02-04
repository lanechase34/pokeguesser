from __future__ import annotations
from datetime import date, timedelta
from unittest.mock import MagicMock, patch
from decimal import Decimal
import pytest
from guesser.cron import SelectDailyPokemonCron
from guesser.models import DailyPokemon, Pokemon


# SelectDailyPokemonCron Tests
@pytest.mark.django_db
class TestSelectDailyPokemonCron:
    """Test the nightly cron job that selects daily Pokemon."""

    def test_cron_has_correct_schedule(self) -> None:
        """Test that cron is scheduled to run at midnight UTC."""
        cron = SelectDailyPokemonCron()
        assert cron.RUN_AT_TIMES == ["00:00"]

    def test_cron_has_correct_code(self) -> None:
        """Test that cron has the correct job code."""
        cron = SelectDailyPokemonCron()
        assert cron.code == "pokemon.select_daily_pokemon"

    def test_cron_creates_pokemon_for_tomorrow(
        self, live_pokemon: list[Pokemon]
    ) -> None:
        """Test that cron selects Pokemon for the next day."""
        cron = SelectDailyPokemonCron()
        tomorrow = date.today() + timedelta(days=1)

        # Ensure tomorrow's pokemon doesn't exist yet
        assert not DailyPokemon.objects.filter(date=tomorrow).exists()

        cron.do()

        # Verify tomorrow's pokemon was created
        assert DailyPokemon.objects.filter(date=tomorrow).exists()
        daily = DailyPokemon.objects.get(date=tomorrow)
        assert daily.pokemon in [p.id for p in live_pokemon]

    def test_cron_does_not_create_duplicate_for_tomorrow(
        self, live_pokemon: list[Pokemon]
    ) -> None:
        """Test that running cron twice doesn't create duplicates."""
        cron = SelectDailyPokemonCron()
        tomorrow = date.today() + timedelta(days=1)

        # Run cron twice
        cron.do()
        first_pokemon = DailyPokemon.objects.get(date=tomorrow).pokemon

        cron.do()
        second_pokemon = DailyPokemon.objects.get(date=tomorrow).pokemon

        # Should be the same pokemon, only one record
        assert first_pokemon == second_pokemon
        assert DailyPokemon.objects.filter(date=tomorrow).count() == 1

    @patch("guesser.cron.GuesserService.create_random_pokemon")
    def test_cron_calls_service_with_correct_parameters(
        self, mock_create: MagicMock, live_pokemon: list[Pokemon]
    ) -> None:
        """Test that cron calls GuesserService with correct arguments."""
        cron = SelectDailyPokemonCron()
        tomorrow = date.today() + timedelta(days=1)

        # Mock the service to return a fake DailyPokemon
        mock_daily = DailyPokemon(date=tomorrow, pokemon=live_pokemon[0].id)
        mock_create.return_value = mock_daily

        cron.do()

        # Verify service was called with correct params
        mock_create.assert_called_once_with(target_date=tomorrow, triggered_by="cron")

    @patch("guesser.cron.logger")
    @patch("guesser.cron.GuesserService.create_random_pokemon")
    def test_cron_logs_success(
        self,
        mock_create: MagicMock,
        mock_logger: MagicMock,
        live_pokemon: list[Pokemon],
    ) -> None:
        """Test that cron logs successful Pokemon selection."""
        cron = SelectDailyPokemonCron()
        tomorrow = date.today() + timedelta(days=1)

        mock_daily = DailyPokemon(date=tomorrow, pokemon=live_pokemon[0].id)
        mock_create.return_value = mock_daily

        cron.do()

        # Verify info log was called
        mock_logger.info.assert_called_once()
        log_message = str(mock_logger.info.call_args)
        assert "Cron selected daily pokemon" in log_message
        assert str(live_pokemon[0].id) in log_message
        assert str(tomorrow) in log_message

    @patch("guesser.cron.logger")
    @patch("guesser.cron.GuesserService.create_random_pokemon")
    def test_cron_logs_error_on_failure(
        self, mock_create: MagicMock, mock_logger: MagicMock
    ) -> None:
        """Test that cron logs errors when Pokemon selection fails."""
        cron = SelectDailyPokemonCron()

        mock_create.side_effect = Exception("Database error")

        cron.do()

        # Verify error was logged
        mock_logger.error.assert_called_once()
        log_message = str(mock_logger.error.call_args)
        assert "Cron failed to select daily pokemon" in log_message
        assert "Database error" in log_message

    @patch("guesser.cron.logger")
    @patch("guesser.cron.GuesserService.create_random_pokemon")
    def test_cron_does_not_crash_on_exception(
        self, mock_create: MagicMock, mock_logger: MagicMock
    ) -> None:
        """Test that cron handles exceptions gracefully without crashing."""
        cron = SelectDailyPokemonCron()

        mock_create.side_effect = Exception("Something went wrong")

        # Should not raise - exception is caught and logged
        try:
            cron.do()
        except Exception as e:
            pytest.fail(f"Cron should not raise exceptions, but raised: {e}")

        # Error should be logged
        mock_logger.error.assert_called_once()

    def test_cron_selects_live_genderless_pokemon(
        self, live_pokemon: list[Pokemon]
    ) -> None:
        """Test that cron only selects live, genderless Pokemon."""
        # Create gendered and not live pokemon
        Pokemon.objects.create(
            id=100,
            number=100,
            name="Gendered",
            gender="Female",
            live=True,
            mega=False,
            giga=False,
            type1="Normal",
            type2="",
            sprite="100",
            generation=Decimal("1.0"),
        )
        Pokemon.objects.create(
            id=200,
            number=200,
            name="Dead",
            gender="",
            live=False,
            mega=False,
            giga=False,
            type1="Normal",
            type2="",
            sprite="200",
            generation=Decimal("1.0"),
        )

        cron = SelectDailyPokemonCron()
        tomorrow = date.today() + timedelta(days=1)

        cron.do()

        daily = DailyPokemon.objects.get(date=tomorrow)

        # Should be one of the live, genderless pokemon
        assert daily.pokemon in [p.id for p in live_pokemon]
        assert daily.pokemon not in [100, 200]

    @patch("guesser.cron.logger")
    @patch("guesser.cron.GuesserService.create_random_pokemon")
    def test_cron_handles_all_pokemon_used_error(
        self, mock_create: MagicMock, mock_logger: MagicMock
    ) -> None:
        """Test that cron handles the case when all Pokemon have been used."""
        cron = SelectDailyPokemonCron()

        mock_create.side_effect = Exception("All Pokemon have been selected!")

        cron.do()

        # Should log the error without crashing
        mock_logger.error.assert_called_once()
        log_message = str(mock_logger.error.call_args)
        assert "All Pokemon have been selected" in log_message
