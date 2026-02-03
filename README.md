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

## PIP

check updates `pip list --outdated`

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
