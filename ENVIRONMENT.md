# Environment variables

Copy `.env.example` to `.env` in the repository root and replace the placeholder values. Do not commit `.env` or use the example passwords/secrets in a deployed environment.

## Docker Compose

All of these variables are required when running `docker compose up`:

| Variable | Purpose |
| --- | --- |
| `POSTGRES_USER` | PostgreSQL/TimescaleDB username; used by Compose to construct the API's database connection URL. |
| `POSTGRES_PASSWORD` | PostgreSQL/TimescaleDB password; used by Compose to construct the API's database connection URL. |
| `POSTGRES_DB` | Database name; used by Compose to construct the API's database connection URL. |
| `JWT_SECRET_KEY` | Secret key Flask-JWT-Extended uses to sign access tokens. Use a long, unique, randomly generated value. |
| `AGENT_PASSWORD` | Shared password expected by the agent login endpoint. Use a strong, unique value. |

Compose constructs `DATABASE_URL` from the three `POSTGRES_*` variables, so you do not need to set `DATABASE_URL` for this setup.

## Running the API directly

When running the API outside Docker Compose, these are required:

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy connection URL for a running PostgreSQL/TimescaleDB database. |
| `JWT_SECRET_KEY` | Secret key Flask-JWT-Extended uses to sign access tokens. |
| `AGENT_PASSWORD` | Shared password expected by the agent login endpoint. |

For this setup, configure `DATABASE_URL` in `.env`; the `POSTGRES_*` variables are not read by the application directly. The database must already be running, and its URL must include valid credentials and database name. Initialize the schema with `python scripts/init_db.py` before starting the API.

`JWT_SECRET_KEY` and `AGENT_PASSWORD` are read from the process environment by the application. Keep their real values private and do not reuse the example placeholders.
