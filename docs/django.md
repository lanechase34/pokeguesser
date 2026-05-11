# Django Guide

This document covers useful Django related commands and features

## Database Overview

- Each 'app' defines database models in models.py
- After updating models.py, create migration files using
  `python manage.py makemigrations ${appname}`
- Check code using
  `python manage.py check`
- Check pending migrations using
  `python manage.py showmigrations --plan`
- Run pending migrations using
  `python manage.py migrate`

## API

- `python manage.py shell` opens Python shell using django information from `manage.py` and auto imports the apps

## Management Commands

These commands are ran directly against the Django shell. The commands are stored in each app in the `mangement/commands` folder.

- Select today's pokemon, can pass in `--date` arg to select another date's

    ```
    python manage.py select_daily_pokemon

    python manage.py select_daily_pokemon --date 05/06/2026
    ```

- Use shell to query and inspect records `python manage.py shell`

    ```
    from guesser.models import DailyPokemon, Pokemon
    from datetime import date

    # Get today's DailyPokemon
    daily = DailyPokemon.objects.get(date=date.today())

    # View the record
    print(f"Date: {daily.date}")
    print(f"Pokemon ID: {daily.pokemon}")
    print(f"Created: {daily.created}")

    # Get the actual Pokemon it refers to
    pokemon = daily.get_pokemon()
    print(f"Pokemon Name: {pokemon.name}")
    print(f"Pokemon Number: {pokemon.number}")
    print(f"Type: {pokemon.type1}/{pokemon.type2}")

    # Or use the string representation
    print(str(daily))
    ```

- Create silhoutte images for the guessing screen. Pass in `--generation` arg to select the generation. This will write the images to the `/frontend/public/silhouettes` directory. The images are written using the PK of the Pokemon record. The actually images in `/frontend/public/images` use the number of the Pokemon. This requires setting the `MAGICK_PATH` environment variable to a valid magick installation `.exe`.

    ```
    python manage.py generate_silhouettes --generation 1
    ```

- Convert `.png` images in `/frontend/public/images` to `.webp`. Optional arguments `--keep-originals` to preserve original `.png` images. `--quality` to override the quality of the conversion, defaults to `80`.

    ```
    python manage.py convert_images_to_webp
    ```