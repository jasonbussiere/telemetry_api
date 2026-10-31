# Telemetry API

A Python-based telemetry system designed to collect, store, and visualize machine performance data from remote agents. The project captures metrics such as CPU usage, RAM usage, and storage information, then exposes them through a REST API and a dashboard for monitoring and analysis.

## Overview

This project was created to explore telemetry ingestion, backend API design, and real-time data collection in a practical environment. Remote agents periodically send hardware and system metrics to the API, which stores the data in a database and makes it available to a frontend dashboard for visualization.

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
- FastAPI or Flask-based API layer
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
│   ├── app.py
│   ├── routes/
│   ├── models/
│   └── services/
├── agents/
│   └── collector.py
├── dashboard/
│   ├── static/
│   └── templates/
├── db/
│   └── models/
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── requirements.txt
├── README.md
└── .gitignore
```

## Local Setup

### Prerequisites

- Python 3.10+
- Docker and Docker Compose
- PostgreSQL or TimescaleDB

### 1. Clone the repository

```bash
git clone https://github.com/jasonbussiere/telemetry_api.git
cd telemetry_api
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file with your database and application settings, for example:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=telemetry
DB_USER=postgres
DB_PASSWORD=your_password
```

### 5. Start the application

```bash
python app.py
```

Or, using Docker:

```bash
docker-compose up --build
```

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
