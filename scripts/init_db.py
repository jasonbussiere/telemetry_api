import os
import sys
from pathlib import Path

project_root=Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from flask import Flask
from dotenv import load_dotenv
from sqlalchemy import text
from db.database import db
from model.models import MetricLog, Agent

load_dotenv()
app = Flask(__name__)
app.config.from_mapping(
    SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)

print("ENV DATABASE_URL:", os.getenv('DATABASE_URL'))
print("DB URI:", app.config['SQLALCHEMY_DATABASE_URI'])

db.init_app(app)

with app.app_context():
    print("Creating tables...")
    db.create_all()

    print("Converting metric_log to TimescaleDB hypertable...")
    try:
        hypertable_sql = text(
            "SELECT create_hypertable('metric_log', 'time', if_not_exists=>TRUE);"
        )
        db.session.execute(hypertable_sql)
        db.session.commit()
        print("Hypertable initialized.")
    except Exception as e:
        db.session.rollback()
        print(f"Hypertable notice: {e}")
