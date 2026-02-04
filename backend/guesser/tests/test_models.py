from __future__ import annotations
from datetime import date, timedelta
import pytest
from django.db import IntegrityError
from django.utils import timezone
from guesser.models import Pokemon, DailyPokemon


# Pokemon Model Tests
@pytest.mark.django_db
class TestPokemonModel:
    """Test Pokemon model behavior"""

    def test_pokemon_meta_db_table(self) -> None:
        """Test Pokemon uses correct database table name"""
        assert Pokemon._meta.db_table == "pokemon"

    def test_pokemon_meta_managed_is_false(self) -> None:
        """Test Pokemon model is not managed by Django"""
        assert Pokemon._meta.managed is False

    def test_pokemon_meta_default_permissions_empty(self) -> None:
        """Test Pokemon has no default permissions"""
        assert Pokemon._meta.default_permissions == ()


# DailyPokemon Model Tests
@pytest.mark.django_db
class TestDailyPokemonModel:
    """Test DailyPokemon model behavior and methods"""

    def test_create_daily_pokemon(self, live_pokemon: list[Pokemon]) -> None:
        """Test creating a DailyPokemon record"""
        today = date.today()
        daily = DailyPokemon.objects.create(date=today, pokemon=live_pokemon[0].id)

        assert daily.date == today
        assert daily.pokemon == live_pokemon[0].id
        assert daily.created is not None

    def test_daily_pokemon_created_auto_set(self, live_pokemon: list[Pokemon]) -> None:
        """Test that created timestamp is automatically set"""
        before = timezone.now()
        daily = DailyPokemon.objects.create(
            date=date.today(), pokemon=live_pokemon[0].id
        )
        after = timezone.now()

        assert before <= daily.created <= after

    def test_daily_pokemon_date_unique_constraint(
        self, live_pokemon: list[Pokemon]
    ) -> None:
        """Test that date field has unique constraint"""
        today = date.today()
        DailyPokemon.objects.create(date=today, pokemon=live_pokemon[0].id)

        with pytest.raises(IntegrityError):
            DailyPokemon.objects.create(date=today, pokemon=live_pokemon[1].id)

    def test_daily_pokemon_different_dates_allowed(
        self, live_pokemon: list[Pokemon]
    ) -> None:
        """Test that different dates can have different pokemon"""
        today = date.today()
        tomorrow = today + timedelta(days=1)

        daily1 = DailyPokemon.objects.create(date=today, pokemon=live_pokemon[0].id)
        daily2 = DailyPokemon.objects.create(date=tomorrow, pokemon=live_pokemon[1].id)

        assert daily1.pokemon != daily2.pokemon
        assert DailyPokemon.objects.count() == 2

    def test_get_pokemon_returns_pokemon_instance(
        self, live_pokemon: list[Pokemon]
    ) -> None:
        """Test get_pokemon() helper method returns Pokemon"""
        daily = DailyPokemon.objects.create(
            date=date.today(), pokemon=live_pokemon[0].id
        )

        pokemon = daily.get_pokemon()

        assert pokemon is not None
        assert isinstance(pokemon, Pokemon)
        assert pokemon.id == live_pokemon[0].id

    def test_get_pokemon_returns_none_for_invalid_id(self) -> None:
        """Test get_pokemon() returns None when Pokemon doesn't exist"""
        daily = DailyPokemon.objects.create(date=date.today(), pokemon=9999)

        pokemon = daily.get_pokemon()

        assert pokemon is None

    def test_pokemon_name_property_returns_name(
        self, live_pokemon: list[Pokemon]
    ) -> None:
        """Test pokemon_name property returns the Pokemon's name"""
        daily = DailyPokemon.objects.create(
            date=date.today(), pokemon=live_pokemon[0].id
        )

        assert daily.pokemon_name == live_pokemon[0].name

    def test_pokemon_name_property_returns_none_for_invalid_id(self) -> None:
        """Test pokemon_name property returns None when Pokemon doesn't exist"""
        daily = DailyPokemon.objects.create(date=date.today(), pokemon=9999)

        assert daily.pokemon_name is None

    def test_daily_pokemon_str_representation(
        self, live_pokemon: list[Pokemon]
    ) -> None:
        """Test DailyPokemon __str__ returns formatted string"""
        today = date.today()
        daily = DailyPokemon.objects.create(date=today, pokemon=live_pokemon[0].id)

        expected = f"{today} - {live_pokemon[0].name}"
        assert str(daily) == expected

    def test_daily_pokemon_str_with_invalid_pokemon(self) -> None:
        """Test DailyPokemon __str__ handles invalid pokemon gracefully"""
        today = date.today()
        daily = DailyPokemon.objects.create(date=today, pokemon=9999)

        expected = f"{today} - None"
        assert str(daily) == expected

    def test_daily_pokemon_meta_db_table(self) -> None:
        """Test DailyPokemon uses correct database table name"""
        assert DailyPokemon._meta.db_table == "daily_pokemon"

    def test_daily_pokemon_can_reuse_same_pokemon_different_dates(
        self, live_pokemon: list[Pokemon]
    ) -> None:
        """Test that same Pokemon can be used on different dates"""
        today = date.today()
        tomorrow = today + timedelta(days=1)

        daily1 = DailyPokemon.objects.create(date=today, pokemon=live_pokemon[0].id)
        daily2 = DailyPokemon.objects.create(date=tomorrow, pokemon=live_pokemon[0].id)

        assert daily1.pokemon == daily2.pokemon
        assert daily1.date != daily2.date


# Database Router Tests
@pytest.mark.django_db
class TestDatabaseRouter:
    """Test database routing configuration"""

    def test_pokemon_writes_blocked_in_production(self) -> None:
        """
        Test that Pokemon writes would be blocked by router in production.
        Note: This test documents the intended behavior but cannot test
        the actual router since it's disabled in conftest for testing.
        """
        # In production with router enabled, this would fail
        # In tests with router disabled (via conftest), this succeeds
        # This test documents expected production behavior
        from config.db_router import DatabaseRouter

        router = DatabaseRouter()

        # Router should return None for Pokemon writes (blocking them)
        result = router.db_for_write(Pokemon)
        assert result is None

    def test_daily_pokemon_writes_allowed(self) -> None:
        """Test that DailyPokemon writes go to default database"""
        from config.db_router import DatabaseRouter

        router = DatabaseRouter()

        result = router.db_for_write(DailyPokemon)
        assert result == "default"

    def test_pokemon_reads_from_pogotracker_db(self) -> None:
        """Test that Pokemon reads route to pogotracker_db"""
        from config.db_router import DatabaseRouter

        router = DatabaseRouter()

        # In production, Pokemon reads would go to pogotracker_db
        # This tests the router logic, not actual database access
        result = router.db_for_read(Pokemon)
        assert result == "pogotracker_db"

    def test_daily_pokemon_reads_from_default(self) -> None:
        """Test that DailyPokemon reads come from default database"""
        from config.db_router import DatabaseRouter

        router = DatabaseRouter()

        result = router.db_for_read(DailyPokemon)
        assert result == "default"

    def test_router_blocks_pokemon_migrations(self) -> None:
        """Test that Pokemon table is never migrated"""
        from config.db_router import DatabaseRouter

        router = DatabaseRouter()

        # Should return False for any database
        assert router.allow_migrate("default", "guesser", "pokemon") is False
        assert router.allow_migrate("pogotracker_db", "guesser", "pokemon") is False

    def test_router_allows_daily_pokemon_migrations_on_default(self) -> None:
        """Test that DailyPokemon can be migrated on default database"""
        from config.db_router import DatabaseRouter

        router = DatabaseRouter()

        assert router.allow_migrate("default", "guesser", "dailypokemon") is True

    def test_router_blocks_migrations_on_non_default_db(self) -> None:
        """Test that non-Pokemon models can't migrate to pogotracker_db"""
        from config.db_router import DatabaseRouter

        router = DatabaseRouter()

        assert (
            router.allow_migrate("pogotracker_db", "guesser", "dailypokemon") is False
        )
