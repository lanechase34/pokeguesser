from __future__ import annotations
import argparse
from django.core.management.base import BaseCommand
from pathlib import Path
from guesser.models import Pokemon


class Command(BaseCommand):
    help = "Rename Pokemon silhouette images based on database IDs"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "generation", type=float, help="Pokemon generation (e.g., 1, 1.5, 2)"
        )

    def handle(self, *args: str, **options: str) -> None:
        generation = options["generation"]

        # Validate decimal points
        generation_str = str(generation)
        if "." in generation_str and len(generation_str.split(".")[1]) > 1:
            self.stdout.write(
                self.style.ERROR("Generation must have at most 1 decimal point")
            )
            return

        # Path to silhouettes folder
        # Adjust this path based on your project structure
        silhouettes_dir = (
            Path(__file__).resolve().parent.parent.parent.parent.parent
            / "frontend"
            / "public"
            / "silhouettes"
        )

        if not silhouettes_dir.exists():
            self.stdout.write(
                self.style.ERROR(
                    f"Silhouettes directory not found at {silhouettes_dir}"
                )
            )
            return

        # Load Pokemon from database
        pokemon_list = Pokemon.objects.filter(
            generation=generation, mega=False, giga=False
        ).values("id", "number", "name")

        self.stdout.write(
            f"Found {len(pokemon_list)} Pokemon for generation {generation}"
        )

        renamed_count = 0
        not_found_count = 0

        for pokemon in pokemon_list:
            pokemon_id = pokemon["id"]
            pokemon_number = pokemon["number"]
            pokemon_name = pokemon["name"]

            # Pad number with leading zeros (max 3 digits)
            padded_number = str(pokemon_number).zfill(3)

            # Check if image exists
            old_filename = f"{padded_number}.png"
            old_path = silhouettes_dir / old_filename

            if old_path.exists():
                # Rename to pokemon ID
                new_filename = f"{pokemon_id}.png"
                new_path = silhouettes_dir / new_filename

                # Check if target file already exists
                if new_path.exists():
                    self.stdout.write(
                        self.style.WARNING(
                            f"Skipping {old_filename}: {new_filename} already exists"
                        )
                    )
                    continue

                # Rename the file
                old_path.rename(new_path)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Renamed: {old_filename} -> {new_filename} ({pokemon_name}, ID {pokemon_id})"
                    )
                )
                renamed_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Image not found: {old_filename} ({pokemon_name}, ID {pokemon_id})"
                    )
                )
                not_found_count += 1

        self.stdout.write(self.style.SUCCESS("\n=== Summary ==="))
        self.stdout.write(self.style.SUCCESS(f"Renamed: {renamed_count}"))
        self.stdout.write(self.style.WARNING(f"Not found: {not_found_count}"))
