1. Update your vscode user preferences
   `Ctrl + Shift + P` -> Open user settings (JSON)

Add this line to the bottom
`"python.venvPath": "${workspaceFolder}/backend"`

2.  Copy .env.example to .env and populate

Create virtual environment to run code

python -m venv backend/dev

Activate the virtual environment

backend/dev\Scripts\activate

To deactivate, run

deactivate

- Open python file, in bottom right where python version is listed, click that
- 'Select a python environment' will pop-up - select the dev venv we set up aboev
- Subsequent vscode opens should auto run the activate for you and adjust the terminals for it

4. Install dependencies

    `pip install -r requirements.txt`

    `pip install -r requirements-dev.txt`

Start server

python manage.py runserver

## PIP

check updates `pip list --outdated`

Init cache table?
`python manage.py createcachetable cache_table`

### Database overview

- Each 'app' defines database models in models.py
- After updating models.py, create migration files using
  `python manage.py makemigrations ${appname}`
- Check code using
  `python manage.py check`
- Check pending migrations using
  `python manage.py showmigrations --plan`
- Run pending migrations using
  `python manage.py migrate`

### Django API

- `python manage.py shell` opens python shell using django information from manage.py and auto imports the apps

### Testing

- Tests should be organized in a tests/ directory with each test being ${name}\_test.py  
  `python manage.py test ${test_name}`

### Management commands

- Select today's pokemon, can pass in --date arg to select another date's
  `python manage.py select_daily_pokemon`

- Use shell to query and inspect records
  `python manage.py shell`
    - select a record for example:

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

    image magick make black silhoutte of image

    `magick input.png -channel RGB -evaluate set 0 +channel output.png`

### Testing

Copy the docker/.env.testing.example to /backend/.env.test

This will allow tests to run locally and connect to docker containers

Test database will automatically be created as 'test_pokeguesser'

### Python dev

Type check files using mypy

Run task -> Type Check Python Files

Format using ruff

Run Task -> Format Python Files

Lint using ruff

Run Task -> Lint Python Files

Pre-commit formatting, linting, and type checking. Setup githooks by running

`pre-commit install`

To run before commit, use

`pre-commit run --all-files`
