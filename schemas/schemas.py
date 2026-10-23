from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import Schema, fields
from db.database import db
from model.models import Agent, MetricLog

class AgentSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Agent
        load_instance = True
        sqla_session = db.session

class MetricLogSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = MetricLog
        load_instance = True
        sqla_session = db.session
class TelemetryIngestSchema(Schema):
    hostname = fields.Str(required=True)
    cpu_percent = fields.Float(required=True)
    ram_percent = fields.Float(required=True)
    disk_percent = fields.Float(required=True)
    total_ram_gb = fields.Float(required=True)
    total_disk_gb = fields.Float(required=True)
    os_info = fields.Str(required=True)
    status = fields.Str(required=True)

agent_schema = AgentSchema()
metric_schema = MetricLogSchema()
metrics_schema = MetricLogSchema(many=True)
ingest_schema = TelemetryIngestSchema()
