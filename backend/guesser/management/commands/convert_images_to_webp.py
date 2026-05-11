from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Convert PNG images to WebP format using ImageMagick"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--quality",
            type=int,
            default=80,
            help="WebP quality (0-100, default: 80)",
        )
        parser.add_argument(
            "--keep-originals",
            action="store_true",
            help="Keep original PNG files after conversion",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        quality = options["quality"]
        keep_originals = options["keep_originals"]

        # ImageMagick path
        magick_path = settings.MAGICK_PATH
        if not magick_path:
            self.stdout.write(self.style.ERROR("MAGICK_PATH not defined"))
            return

        # Path to images folder
        images_dir = (
            Path(__file__).resolve().parent.parent.parent.parent.parent
            / "frontend"
            / "public"
            / "images"
        )

        # Validate directory
        if not images_dir.exists():
            self.stdout.write(
                self.style.ERROR(f"Images directory not found at {images_dir}")
            )
            return

        png_files = list(images_dir.glob("*.png"))

        if not png_files:
            self.stdout.write(
                self.style.WARNING("No PNG files found in images directory")
            )
            return

        self.stdout.write(f"Found {len(png_files)} PNG files to convert")

        converted_count = 0
        skipped_count = 0
        error_count = 0

        for png_path in png_files:
            webp_path = png_path.with_suffix(".webp")

            # Skip if webp already exists
            if webp_path.exists():
                self.stdout.write(
                    self.style.WARNING(
                        f"WebP already exists, skipping: {webp_path.name}"
                    )
                )
                skipped_count += 1
                continue

            try:
                subprocess.run(
                    [
                        magick_path,
                        str(png_path),
                        "-quality",
                        str(quality),
                        str(webp_path),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )

                if not keep_originals:
                    png_path.unlink()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Converted and deleted: "
                            f"{png_path.name} -> {webp_path.name}"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Converted: {png_path.name} -> {webp_path.name}"
                        )
                    )

                converted_count += 1
            except subprocess.CalledProcessError as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"ImageMagick error for {png_path.name}: {e.stderr}"
                    )
                )
                error_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Unexpected error converting {png_path.name}: {str(e)}"
                    )
                )
                error_count += 1

        self.stdout.write(self.style.SUCCESS("\n=== Summary ==="))
        self.stdout.write(self.style.SUCCESS(f"Converted: {converted_count}"))
        self.stdout.write(
            self.style.WARNING(f"Skipped (already exist): {skipped_count}")
        )
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f"Errors: {error_count}"))
