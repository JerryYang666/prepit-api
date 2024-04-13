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

## Setup

### Required Software

- Docker
- Postgresql
- Python (version 3.11.0)

### Local Database

For security reasons we cannot just connect to the live database so instead we use a local postgresql database

  

To set this up start by running pgadmin4 (should have came with postgresql). If it is your first time running postgresql it will ask you to set up a password, this will be used later. Once in pgadmin, create a new database called `ai4edu_local`. Afterwards right click the database and hit create script. Copy the following into the script and press execute

````
create table db_version
(
version varchar(15) not null
constraint db_version_pk
primary key
);
  
create table ai_agents
(
agent_id uuid not null
constraint ai_agents_pk
primary key,
created_at timestamp default now() not null,
agent_name varchar(255) not null,
course_id varchar(31),
creator varchar(16),
updated_at timestamp default now() not null,
voice boolean default false not null,
status integer default 1 not null,
allow_model_choice boolean default true not null,
model varchar(16)
);
````

### .env

The .env file contains sensitive information such as API keys and is thus not kept in the repo. Create a new file named `.env` and copy in the keys (it should be on slack but if you cant find just ask). Replace the make DB_URI equal `postgresql+psycopg://postgres:your_postgresql_password@host.docker.internal:5432/prepit_local`

Make sure to replace your_postgresql_password with your actual postgresql password.

## Run the backend

In order to start the backend make sure you have Docker running and use the command `docker compose up --build`

Alternatively if you want to run the backend outside of docker you can use `python run_server_local.py` or `python3 run_server_local.py` (the command depends on how python is setup on your machine). Note that if you run it outside of Docker you need to change the DB_URI in the .env file to `postgresql+psycopg://postgres:your_postgresql_password@localhost:5432/prepit_local`