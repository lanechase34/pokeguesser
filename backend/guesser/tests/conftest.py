from __future__ import annotations
from typing import Any, Generator
import pytest
from django.conf import settings
from django.db import connections, connection
from guesser.models import Pokemon, DailyPokemon
from datetime import date


def pytest_configure() -> None:
    """Disable database routers for tests and uses in-memory cache"""
    settings.DATABASE_ROUTERS = []
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }


@pytest.fixture(scope="session", autouse=True)
def create_pokemon_table(
    django_db_setup: Any, django_db_blocker: Any
) -> Generator[None, None, None]:
    """
    Create the unmanaged Pokemon table in the test database.
    This runs once per test session.
    """
    from guesser.models import Pokemon

    with django_db_blocker.unblock():
        connection = connections["default"]

        existing_tables = connection.introspection.table_names()
        if "pokemon" not in existing_tables:
            with connection.schema_editor() as schema_editor:
                schema_editor.create_model(Pokemon)

    yield


@pytest.fixture(autouse=True)
def clear_test_data_between_tests(db: None) -> Generator[None, None, None]:
    """
    Clear Pokemon and DailyPokemon records between tests
    This is needed when we are testing REAL commits using @pytest.mark.django_db(transaction=True)
    """
    yield
    from guesser.models import DailyPokemon, Pokemon
    from django.core.cache import cache

    DailyPokemon.objects.all().delete()
    Pokemon.objects.all().delete()
    cache.clear()


# Fixtures
# Sets up resources used throughout tests
@pytest.fixture
def live_pokemon(db: None) -> list[Pokemon]:
    """Create a set of live, genderless Pokemon for selection"""
    assert "test_" in connection.settings_dict["NAME"]
    pokemon_list: list[Pokemon] = []
    for i in range(1, 6):
        pokemon_list.append(
            Pokemon.objects.create(
                id=i,
                name=f"Pokemon{i}",
                number=i,
                gender="",
                live=True,
                mega=False,
                giga=False,
                type1="Normal",
                type2="",
                sprite=str(i),
                generation=1,
            )
        )
    return pokemon_list


@pytest.fixture
def gendered_pokemon(db: None) -> Pokemon:
    """Pokemon with a gender value - should be excluded from random selection"""
    return Pokemon.objects.create(
        id=100,
        name="Nidoran\u2640",
        number=29,
        gender="Female",
        live=True,
        mega=False,
        giga=False,
        type1="Poison",
        type2="",
        generation=1,
    )


@pytest.fixture
def not_live_pokemon(db: None) -> Pokemon:
    """Pokemon with live=False - should be excluded from random selection"""
    return Pokemon.objects.create(
        id=200,
        name="NotYetLiveMon",
        number=200,
        gender="",
        live=False,
        mega=False,
        giga=False,
        sprite="200",
        generation=1,
    )


@pytest.fixture
def today_pokemon(db: None, live_pokemon: list[Pokemon]) -> DailyPokemon:
    """A DailyPokemon already assigned for today"""
    return DailyPokemon.objects.create(date=date.today(), pokemon=live_pokemon[0].id)
