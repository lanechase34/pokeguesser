import logging
from datetime import date, timedelta

from .services import GuesserService

logger = logging.getLogger(__name__)


class SelectDailyPokemonCron:
    RUN_AT_TIMES = ["00:00"]  # Midnight UTC, generate the next day's pokemon
    code = "pokemon.select_daily_pokemon"

    def do(self) -> None:
        """
        Automatically select next day's pokemon every night
        """
        try:
            daily_pokemon = GuesserService.create_random_pokemon(
                target_date=date.today() + timedelta(days=1),
                triggered_by="cron",
            )
            logger.info(
                f"Cron selected daily pokemon: {daily_pokemon.pokemon} "
                f"for {daily_pokemon.date}"
            )
        except Exception as e:
            logger.error(f"Cron failed to select daily pokemon: {e}", exc_info=True)
