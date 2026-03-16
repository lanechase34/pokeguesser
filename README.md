## First Time Dev Setup

### Prerequisites

- Python >=3.14
- Node >=24

1. Configure VSCode Python Settings

    Update VSCode preferences to look for virtual Python environment.

    ```
    `Ctrl + Shift + P` -> Open user settings (JSON)

    Add this line to the bottom
    `"python.venvPath": "${workspaceFolder}/backend"`
    ```

2. Create Python Virtual Environment

    Run the following from the **project root**:

    ```bash
    python -m venv backend/dev
    ```

    > This creates a `dev/` folder inside `backend/` containing a local Python installation

3. Activate the Virtual Environment

    Open a new bash terminal inside VSCode. The virtual environment should activate
    automatically — you'll know it's working when you see **(dev)** at the start of your
    terminal prompt:

    ```
    (dev) PS C:\Users\...\pokeguesser>
    ```

    > If **(dev)** doesn't appear, try closing and reopening the terminal. If it still doesn't
    > appear, run the activation script manually:
    >
    > ```bash
    > backend/dev/Scripts/Activate.ps1
    > ```

4. Install Python Dependencies from /backend

    ```bash
    cd /backend
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    ```

5. Install NPM Depdendencies from /frontend

    ```bash
    npm install
    ```

6. Setup GitHooks from project root

    ```bash
    npm install -g lefthook
    lefthook install
    ```

7. Configure Environment

    Copy `docker/.env.docker.example` to `backend/.env.docker`

    ```bash
      cp backend/.env.docker.example backend/.env.docker
    ```

    > Modify the variables as needed

8. Start Application with Docker

    Navigate to Docker dir

    ```bash
    cd docker
    ```

    Start all services in detached mode (runs in the background):

    ```bash
    docker compose up -d
    ```

    > **First run:** Docker will build the frontend and backend images automatically.

    > This may take a few minutes. Subsequent runs will use cached images and start much faster.

9. Verify the Application is Running

    Once the containers have started, confirm everything is working by visiting:

    | Service              | URL                                      |
    | -------------------- | ---------------------------------------- |
    | Frontend             | http://localhost:3001                    |
    | Backend Health Check | http://localhost:8085/api/v1/healthcheck |

    ***

10. Stop Application By Running

    ```bash
    docker compose down
    ```

### NEEDS FORMATTED

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
