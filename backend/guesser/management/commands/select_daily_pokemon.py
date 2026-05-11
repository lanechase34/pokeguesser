from __future__ import annotations

import argparse
from datetime import datetime
from typing import Any

from django.core.management.base import BaseCommand
from django.utils import timezone

from guesser.services import GuesserService


class Command(BaseCommand):
    help = "Manually select the daily pokemon for a given date"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--date", type=str, help="Date in YYYY-MM-DD format (defaults to today)"
        )

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            target_date = (
                datetime.strptime(options["date"], "%Y-%m-%d").date()
                if options["date"]
                else timezone.now().date()
            )

            daily_pokemon = GuesserService.create_random_pokemon(
                target_date, triggered_by="manual_command"
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Selected pokemon ID {daily_pokemon.pokemon} "
                    f"for {daily_pokemon.date}"
                )
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed: {str(e)}"))
            raise
