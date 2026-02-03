from django_cron import CronJobBase, Schedule
from .services import GuesserService
from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)


class SelectDailyPokemonCron(CronJobBase):
    RUN_AT_TIMES = ["00:00"]  # Midnight UTC, generate the next day's pokemon
    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = "pokemon.select_daily_pokemon"

    def do(self):
        """
        Automatically select next day's pokemon every night
        """
        try:
            daily_pokemon = GuesserService.create_random_pokemon(
                target_date=date.today() + timedelta(days=1),
                triggered_by="cron",
            )
            logger.info(
                f"Cron selected daily pokemon: {daily_pokemon.pokemon} for {daily_pokemon.date}"
            )
        except Exception as e:
            logger.error(f"Cron failed to select daily pokemon: {e}", exc_info=True)
