# Prepit API container

## This is the repo for the prepit experimental project.
- The main entry point is main.py. This is the fastapi app that serves the API.
- To run a local instance of the app, run "run_server_local.py"
- In the cloud deployment environment, the app is run as a docker container. The docker image is built using the Dockerfile in the root directory of this repo. The docker image is then pushed to the GitHub container registry (https://ghcr.io). The docker image is then pulled from the registry and run as a container in the cloud deployment environment.
- The "admin" folder contains the admin service code.
- The "user" folder contains the end user code.
- The "common" folder contains common classes.

## Config files
There are two config files maintained in this repo:
- the docker_compose_cloud folder contains the docker compose file for the cloud deployment environment
- the nginx_conf folder contains the nginx configuration file for the cloud deployment environment. In the cloud deployment environment, the nginx server (running as a docker container) is used as a reverse proxy server to the fastapi app.

## Database connection and migration
The database connection and migration is handled by 3 packages:
- alembic: database migration
- sqlalchemy: ORM (Object Relational Mapping)
- psycopg: database connection
The alembic configuration file is maintained in the root directory of this repo. The database migration scripts are maintained in the "migrations" folder in the root directory of this repo.
Alembic is used to generate the migration scripts. The migration scripts are then run in the cloud deployment environment to update the database schema.
All database models are maintained in the "models.py" file in the "migration" folder.