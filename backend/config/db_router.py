from typing import Any

from django.db import models


class DatabaseRouter:
    """
    Route database operations based on model.
    DailyPokemon -> default (guesser db)
    Pokemon -> read-only from pogotracker_db
    """

    def db_for_read(self, model: type[models.Model], **hints: Any) -> str:
        """Route reads"""
        if model._meta.app_label == "guesser" and model._meta.model_name == "pokemon":
            return "pogotracker_db"
        return "default"

    def db_for_write(self, model: type[models.Model], **hints: Any) -> str | None:
        """Route writes"""
        if model._meta.app_label == "guesser" and model._meta.model_name == "pokemon":
            return None  # prevent any writes to pogotracker_db
        return "default"

    def allow_relation(
        self, obj1: models.Model, obj2: models.Model, **hints: Any
    ) -> bool:
        """Allow relations between objects in the same database"""
        return True

    def allow_migrate(
        self, db: str, app_label: str, model_name: str | None = None, **hints: Any
    ) -> bool:
        """Ensure Pokemon table doesn't get migrated"""
        if model_name == "pokemon":
            return False  # Never migrate Pokemon table
        return db == "default"  # Only migrate other models in default DB
