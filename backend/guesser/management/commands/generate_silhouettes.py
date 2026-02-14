from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

from django.core.management.base import BaseCommand
from dotenv import load_dotenv

from guesser.models import Pokemon

load_dotenv()


class Command(BaseCommand):
    help = "Generate Pokemon silhouettes using ImageMagick"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--generation", type=float, help="Pokemon generation (e.g., 1, 1.5, 2)"
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

        # Paths to images and silhouettes folders
        base_dir = (
            Path(__file__).resolve().parent.parent.parent.parent.parent
            / "frontend"
            / "public"
        )
        images_dir = base_dir / "images"
        silhouettes_dir = base_dir / "silhouettes"

        # ImageMagick path
        magick_path = os.getenv("MAGICK_PATH")

        if not magick_path:
            self.stdout.write(self.style.ERROR("MAGICK_PATH not defined"))
            return

        # Validate directories
        if not images_dir.exists():
            self.stdout.write(
                self.style.ERROR(f"Images directory not found at {images_dir}")
            )
            return

        # Create silhouettes directory if it doesn't exist
        silhouettes_dir.mkdir(parents=True, exist_ok=True)

        # Load Pokemon from database
        pokemon_list = Pokemon.objects.filter(
            generation=generation, mega=False, giga=False
        ).values("id", "number", "name")

        self.stdout.write(
            f"Found {len(pokemon_list)} Pokemon for generation {generation}"
        )

        silhouette_count = 0
        not_found_count = 0
        skipped_count = 0
        error_count = 0

        for pokemon in pokemon_list:
            pokemon_id = pokemon["id"]
            pokemon_number = pokemon["number"]
            pokemon_name = pokemon["name"]

            # Pad number with leading zeros (max 3 digits)
            padded_number = str(pokemon_number).zfill(3)

            # Source file path (original .webp file in images directory by number)
            source_filename = f"{padded_number}.webp"
            source_path = images_dir / source_filename

            if not source_path.exists():
                self.stdout.write(
                    self.style.WARNING(
                        f"Image not found: {source_filename} ({pokemon_name}, "
                        f"ID {pokemon_id})"
                    )
                )
                not_found_count += 1
                continue

            # Silhouette output file (named by pk in silhouettes directory)
            silhouette_filename = f"{pokemon_id}.webp"
            silhouette_path = silhouettes_dir / silhouette_filename

            # Check if silhouette already exists
            if silhouette_path.exists():
                self.stdout.write(
                    self.style.WARNING(
                        f"Silhouette already exists: "
                        f"{silhouette_filename} ({pokemon_name})"
                    )
                )
                skipped_count += 1
                continue

            # Generate silhouette using ImageMagick
            try:
                subprocess.run(
                    [
                        magick_path,
                        str(source_path),
                        "-channel",
                        "RGB",
                        "-evaluate",
                        "set",
                        "0",
                        "+channel",
                        str(silhouette_path),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Generated silhouette: "
                        f"{source_filename} -> {silhouette_filename} "
                        f"({pokemon_name}, ID {pokemon_id})"
                    )
                )
                silhouette_count += 1
            except subprocess.CalledProcessError as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"ImageMagick error for {source_filename}: {e.stderr}"
                    )
                )
                error_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Unexpected error generating silhouette"
                        f" for {source_filename}: {str(e)}"
                    )
                )
                error_count += 1

        self.stdout.write(self.style.SUCCESS("\n=== Summary ==="))
        self.stdout.write(
            self.style.SUCCESS(f"Silhouettes generated: {silhouette_count}")
        )
        self.stdout.write(
            self.style.WARNING(f"Already exist (skipped): {skipped_count}")
        )
        self.stdout.write(self.style.WARNING(f"Not found: {not_found_count}"))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f"Errors: {error_count}"))
