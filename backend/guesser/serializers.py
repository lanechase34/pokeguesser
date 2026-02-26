from rest_framework import serializers

from .models import Pokemon


class PokemonSerializer(serializers.ModelSerializer[Pokemon]):
    """
    Serialize for the pokemon
    """

    class Meta:
        model = Pokemon
        fields = ["id", "name", "number", "sprite", "type1", "type2"]
        read_only_fields = fields
