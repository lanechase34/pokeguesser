## First Time Dev Setup

### Prerequisites

- Python >=3.14
- Node >=24

1. Configure VSCode Python Settings

    Update VSCode preferences to look for virtual Python environment.

    ```
    `Ctrl + Shift + P` -> Open user settings (JSON)

    Add this line to the bottom
    "python.venvPath": "${workspaceFolder}/backend"
    ```

2. Create Python Virtual Environment

    Run the following from the **project root**:

    ```bash
    python -m venv backend/dev
    ```

    > This creates a `dev/` folder inside `backend/` containing a local Python installation

3. Activate the Virtual Environment

    Open a new bash terminal inside VSCode. The virtual environment should activate
    automatically - you'll know it's working when you see **(dev)** at the start of your terminal prompt:

    ```
    (dev) PS C:\Users\...\pokeguesser>
    ```

    > If **(dev)** doesn't appear, try closing and reopening the terminal. If it still doesn't
    > appear, run the activation script manually:

    ```bash
    backend/dev/Scripts/Activate.ps1
    ```

4. Install Python Dependencies from /backend

    ```bash
    cd /backend
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    ```

5. Install NPM Depdendencies from /frontend

    ```bash
    cd /frontend
    npm install
    ```

6. Setup GitHooks from project root

    ```bash
    cd ..
    npm install -g lefthook
    lefthook install
    ```

7. Configure Environment

    Copy `docker/.env.docker.example` to `backend/.env.docker`

    ```bash
      cp docker/.env.docker.example backend/.env.docker
    ```

    > Modify the environment variables as needed

    > You will need to set the `SECRET_KEY`

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

### Connecting to the PokeGuesser database

| Setting      | Value             |
| ------------ | ----------------- |
| **Host**     | `localhost`       |
| **Port**     | `5434`            |
| **Database** | `pokeguesser_db`  |
| **Username** | `docker_user1234` |
| **Password** | `docker_pass1234` |
| **Schema**   | `public`          |

### Connecting to the PogoTracker Mock database

| Setting      | Value                        |
| ------------ | ---------------------------- |
| **Host**     | `localhost`                  |
| **Port**     | `5435`                       |
| **Database** | `pokeguesser_pogotracker_db` |
| **Username** | `pogo_docker_user1234`       |
| **Password** | `pogo_docker_pass1234`       |
| **Schema**   | `public`                     |