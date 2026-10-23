from datetime import datetime, timezone

from db.database import db


class Agent(db.Model):
    __tablename__ = 'agent'
    id = db.Column(db.Integer, primary_key=True)
    hostname = db.Column(db.String(100), unique=True, nullable=False)
    os_info = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    metrics = db.relationship('MetricLog', backref='host', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'hostname': self.hostname,
            'os_info': self.os_info,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

class MetricLog(db.Model):
    __tablename__ = 'metric_log'
    time=db.Column(db.DateTime(timezone=True), primary_key=True, default=lambda: datetime.now(timezone.utc))
    agent_id = db.Column(db.Integer, db.ForeignKey('agent.id'), primary_key=True, nullable=False)
    cpu_percent = db.Column(db.Float, nullable=False)
    ram_percent = db.Column(db.Float, nullable=False)
    total_ram_gb = db.Column(db.Float, nullable=False)
    disk_percent = db.Column(db.Float, nullable=False)
    total_disk_gb = db.Column(db.Float, nullable=False)


    def to_dict(self):
        return {
            'timestamp': self.time.isoformat() if self.time else None,
            'agent_id': self.agent_id,
            'cpu_percent': self.cpu_percent,
            'ram_percent': self.ram_percent,
            'total_ram_gb': self.total_ram_gb,
            'disk_percent': self.disk_percent,
            'total_disk_gb': self.total_disk_gb,
        }

