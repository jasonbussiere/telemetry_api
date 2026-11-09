# Telemetry API

A Python-based telemetry system designed to collect, store, and visualize machine performance data from remote agents. The project captures metrics such as CPU usage, RAM usage, and storage information.

## Overview

This project was created to explore telemetry ingestion, backend API design, and real-time data collection in a practical environment. Remote agents periodically send hardware and system metrics to the API.

The system is structured around a clear data flow:

- Remote agents collect system metrics
- Agents send telemetry to the API endpoint
- The API validates and stores the data
- The dashboard queries the stored data and displays it in a usable format

## Features

- Continuous telemetry collection from remote machines
- REST API for receiving sensor and system data
- Database persistence for historical monitoring
- Dashboard for viewing live or recent system usage
- Modular backend design for easier extension
- Docker support for simplified local setup

## Tech Stack

- Python
- Flask
- JavaScript / HTML for dashboard
- PostgreSQL / TimescaleDB
- SQLAlchemy
- Docker / Docker Compose
- Python agents for remote metric collection

## Architecture

The project follows a simple layered approach:

- Agent layer: collects machine metrics and sends them to the server
- API layer: receives and validates incoming telemetry payloads
- Storage layer: saves telemetry data in a database
- Dashboard layer: reads the stored data and displays charts and metrics

## Project Structure

```text
telemetry_api/
├── api/
│   └── app.py
├── db/
├── model/
├── scripts/
│   └── init_db.py
├── static/
├── templates/
├── Dockerfile
├── docker-compose.yaml
├── requirements.txt
└── README.md
```

## Local Setup

### Prerequisites

- Python 3.10+
- Docker and Docker Compose (for the containerized setup)
- PostgreSQL with the TimescaleDB extension (for running the API directly)

### 1. Clone the repository

```bash
git clone https://github.com/jasonbussiere/telemetry_api.git
cd telemetry_api
```

### Run with Docker Compose

The Compose file is `docker-compose.yaml` in the repository root. Create a `.env` file there with the variables used by the database and API services:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=telemetry
JWT_SECRET_KEY=replace_with_a_secret_key
AGENT_PASSWORD=replace_with_an_agent_password
```

Start the database and API from the repository root:

```bash
docker compose up --build
```

Compose starts TimescaleDB and the API, initializes the database tables, and runs the Flask app with Gunicorn. The dashboard is available at <http://localhost:5000> and the Swagger docs at <http://localhost:5000/apidocs>. Stop the services with `Ctrl+C`; use `docker compose down` to remove the containers while retaining the database volume.

### Run the API directly

To run the API outside Docker, first start a PostgreSQL/TimescaleDB instance and create a `.env` file in the repository root. For this setup, configure the database URL rather than the Compose-specific database connection variables:

```env
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/telemetry
JWT_SECRET_KEY=replace_with_a_secret_key
AGENT_PASSWORD=replace_with_an_agent_password
```

Create the database tables and TimescaleDB hypertable, then start Flask from the repository root:

```bash
python scripts/init_db.py
flask --app api.app run --host=0.0.0.0 --port=5000
```

Open <http://localhost:5000> for the dashboard or <http://localhost:5000/apidocs> for the API documentation.

## Example Data Flow

1. Agent collects:
   - CPU usage
   - memory usage
   - disk usage
   - system status

2. Agent sends JSON payload to the API endpoint

3. API validates payload and stores records in the database

4. Dashboard queries the latest telemetry data and renders it

## Use Cases

- system monitoring
- infrastructure observability
- hardware health tracking
- application performance insight
- proof-of-concept telemetry architecture

## Notes

This project is useful as a portfolio piece because it demonstrates:

- backend API design
- data ingestion from external sources
- database integration
- monitoring and visualization concepts
- practical software architecture for observability systems

## License

This project is licensed under the MIT License.

## Contact

- GitHub: https://github.com/jasonbussiere
- Email: jbussiere777@gmail.com
