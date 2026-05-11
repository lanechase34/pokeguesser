from __future__ import annotations

from functools import cached_property

from django.db import models


class Pokemon(models.Model):
    """
    POGOTracker DB Pokemon table
    """

    id = models.IntegerField(primary_key=True)
    number = models.IntegerField()
    name = models.CharField(max_length=50)
    gender = models.CharField(max_length=10)
    live = models.BooleanField()
    mega = models.BooleanField()
    giga = models.BooleanField()
    type1 = models.CharField(max_length=10)
    type2 = models.CharField(max_length=10)
    sprite = models.CharField(max_length=50)
    generation = models.DecimalField(max_digits=2, decimal_places=1)

    class Meta:
        managed = False  # Poke Guesser does not manage this table schema
        db_table = "pokemon"  # Exact table name in pogotracker_db
        default_permissions = ()  # Empty permissions - nothing allowed via admin panel

    def __str__(self) -> str:
        return self.name


class DailyPokemon(models.Model):
    """
    Track the selected pokemon daily
    Track the date for the guess and the created timestamp
    """

    created = models.DateTimeField(auto_now_add=True)  # set once when created
    date = models.DateField(unique=True)
    pokemon = models.IntegerField()

    class Meta:
        db_table = "daily_pokemon"

    def __str__(self) -> str:
        return f"{self.date} - {self.pokemon_name}"

    def get_pokemon(self) -> Pokemon | None:
        """Helper method to fetch Pokemon record from pogotracker_db"""
        try:
            return Pokemon.objects.get(id=self.pokemon)
        except Pokemon.DoesNotExist:
            return None

    @cached_property
    def pokemon_name(self) -> str | None:
        """Quick access to pokemon name"""
        poke: Pokemon | None = self.get_pokemon()
        return poke.name if poke else None
