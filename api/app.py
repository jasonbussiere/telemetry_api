import datetime
import os
from importlib import invalidate_caches

from dotenv import load_dotenv
from flasgger import Swagger, swag_from
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from marshmallow import ValidationError
from schemas.schemas import agent_schema, metric_schema, metrics_schema, ingest_schema

from db.database import db
from model.models import Agent, MetricLog
from scripts import init_db

load_dotenv()

template = {
    "swagger": "2.0",
    "info": {
        "title": "Skynet Telemetry API",
        "description": "API Documentation for Skynet Telemetry Monitoring System",
        "version": "1.0.0",
    },
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
        "name": "Authorization",
        "in": "header",
        "description": "JWT Authorization header using the Bearer token. Example: \"Authorization: Bearer {token}\""
        }
    }
}



app = Flask(__name__, template_folder='../templates', static_folder='../static')
swagger = Swagger(app, template=template)
CORS(app)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#Initialize the rate limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["2000 per day", "100 per hour"],
    storage_uri="memory://" # store hits in RAM
)

db.init_app(app)
jwt = JWTManager(app)

@app.errorhandler(ValidationError)
def handle_marshmallow_validation(err):
    return jsonify({
        'errors': 'Invalid payload',
        'details': err.messages }), 422


@app.route('/api/login', methods=['POST'], strict_slashes=False)
@limiter.limit("30 per minute")
@swag_from({
    'tags': ['Telemetry'],
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'required': True,
        'schema': {
            'type': 'object',
            'properties': {
                'hostname': {'type': 'string', 'example': 'T850 Agent 1'},
                'password': {'type': 'string', 'example': 'password'}
            }
        }
    }],
    'responses': {
        200: {'description': 'Login success, returns access token'},
        400:{'description':'bad request: hostname or password is required'},
        401: {'description': 'Unauthorized: Invalid username or password'},
        429:{'description': 'Too many requests: rate limit exceeded'},
    }
})
def login():

    data = request.get_json(silent=True)

    if not data or not data.get('hostname') or not data.get('password'):
        return jsonify({'message': 'Hostname and password are required'}), 400

    hostname = data.get('hostname')
    password = data.get('password')
    #Verify against the database here
    if  password == os.getenv('AGENT_PASSWORD'):
        access_token=create_access_token(identity=hostname)
        return jsonify(access_token=access_token), 200

    return jsonify({'message': 'Invalid username or password'}), 401

@app.route('/api/metrics', methods=['POST'], strict_slashes=False)
@jwt_required()
@limiter.limit("100 per second")
@swag_from({
    'tags': ['Telemetry'],
    'security': [{'Bearer': []}],
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'required': True,
        'schema': {
            'type': 'object',
            'properties': {
                'hostname': {'type': 'string', 'example': 'skynet-node-01'},
                'cpu_percent': {'type': 'number', 'example': 14.2},
                'ram_percent': {'type': 'number', 'example': 62.3},
                'disk_percent': {'type': 'number', 'example': 45.8}
            }
        }
    }],
    'responses': {
        201: {'description': 'Telemetry data successfully ingested'},
        401: {'description': 'Unauthorized or missing JWT token'},
        422:{'description': 'Invalid JSON payload or missing'},
        429:{'description': 'Too many requests, please try again later'},
        500:{'description': 'Internal server error'}
    }
})
def ingest_telemetry():
    valid_data = ingest_schema.load(request.get_json() or {})

    try:
        hostname = valid_data.get('hostname')
        host = db.session.execute(select(Agent).filter_by(hostname=hostname)).scalar_one_or_none()

        if not host:
            host = Agent(
                hostname=hostname,
                os_info=valid_data.get('os_info'),
                status=valid_data.get('status')
            )
            db.session.add(host)
            db.session.flush()

        new_log = MetricLog(
            agent_id=host.id,
            time=datetime.datetime.now(datetime.timezone.utc),
            cpu_percent=valid_data.get('cpu_percent'),
            ram_percent=valid_data.get('ram_percent'),
            total_ram_gb=valid_data.get('total_ram_gb'),
            disk_percent=valid_data.get('disk_percent'),
            total_disk_gb=valid_data.get('total_disk_gb'),
        )


        db.session.add(new_log)
        db.session.commit()

        return jsonify({
            'message':'Telemetry successfully recorded',
            'log_id': new_log.time.isoformat(),
            'agent_id': host.id
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error during ingestion: {str(e)}'}), 500

@app.route('/api/hosts/<int:agent_id>/history', methods=['GET'], strict_slashes=False)
@jwt_required()
@limiter.limit("30 per minute")
@swag_from({
    'tags': ['Telemetry'],
    'security': [{'Bearer': []}],
    'parameters': [{
        'name': 'agent_id',
        'in': 'path',
        'type': 'integer',
        'required': True,
        'description': 'The unique agent_id of the host'
    },
    {
        'name': 'limit',
        'in': 'query',
        'type': 'integer',
        'required': False,
        'description': 'The maximum number of records to return',
    }],
    'responses': {
        200: {'description': 'TimescaleDB-backed historical metrics timeline'},
        401: {'description': 'Unauthorized or missing JWT token'},
        404: {'description': 'Host not found or does not exist'},
        429: {'description': 'Too many requests: rate limit exceeded'},
    }
})
def get_agent_history(agent_id):
    agent=db.get_or_404(Agent, agent_id)

    limit=request.args.get('limit', 50, type=int)

    stmt = select(MetricLog).filter_by(agent_id=agent_id).order_by(MetricLog.time.desc()).limit(limit)

    logs=db.session.scalars(stmt).all()

    logs.reverse()

    return jsonify({
        'host':agent_schema.dump(agent),
        'history':metrics_schema.dump(logs),
    }), 200

@app.route('/api/hosts', methods=['GET'], strict_slashes=False)
@limiter.limit("100 per minute")
@swag_from({
    'tags': ['Telemetry'],
    'responses': {
        200: {'description': 'List of active hosts reporting metrics'},
        429: {'description': 'Too many requests: rate limit exceeded'},
    }
})
def get_all_agents():
    #fetch all hosts from the database
    hosts = db.session.scalars(select(Agent)).all()
    host_list=[]

    #get current time
    now = datetime.datetime.now(datetime.timezone.utc)

    #grab the lastest metric log for this specific host
    for host in hosts:
        latest_log=host.metrics.order_by(MetricLog.time.desc()).first()

        if not latest_log:
            continue

        log_time=latest_log.time
        if log_time.tzinfo is None:
            log_time=log_time.replace(tzinfo=datetime.timezone.utc)

        time_diff=(now-log_time).total_seconds()

        if time_diff < 30:
            metric_data= metric_schema.dump(latest_log)

            host_list.append({
                'host': agent_schema.dump(host),
                'latest_metric': metric_data,
            })

    return jsonify(host_list), 200

@app.route('/api/hosts/<int:agent_id>', methods=['PUT'], strict_slashes=False)
@jwt_required()
@limiter.limit("10 per minute")
@swag_from({})
@swag_from({
    'tags': ['Telemetry'],
    'security': [{'Bearer': []}],
    'parameters': [{
        'name': 'agent_id',
        'in': 'path',
        'type': 'integer',
        'required': True,
        'description': 'The unique agent_id of the host'
    }],
    'responses': {
        200: {'description': 'Agent successfully updated'},
        400: {'description': 'Invalid payload'},
        401: {'description': 'Unauthorized or missing JWT token'},
        404: {'description': 'Agent not found'},
        422: {'description': 'Invalid JSON payload or missing'},
        429: {'description': 'Too many requests: rate limit exceeded'},
        409: {'description':'Agent with this hostname already exists'},
        500: {'description':'Internal server error'}
    }
})
def update_agent(agent_id):

    agent=db.get_or_404(Agent, agent_id)
    data = request.get_json(silent=True)

    if not data:
        return jsonify({'error': 'Invalid or empty payload'}), 400

    agent =agent_schema.load(request.get_json() or {}, instance=agent, partial=True)

    try:
        db.session.commit()
        return jsonify({
            'message':'Agent successfully updated',
            'host': agent_schema.dump(agent),
        }), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Agent with this hostname already exists'}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Internal server error str{e}'}), 500

@app.route('/api/hosts/<int:agent_id>', methods=['DELETE'], strict_slashes=False)
@jwt_required()
@limiter.limit("10 per minute")
@swag_from({
    'tags': ['Telemetry'],
    'security': [{'Bearer': []}],
    'parameters': [{
        'name': 'agent_id',
        'in': 'path',
        'type': 'integer',
        'required': True,
        'description': 'The unique agent_id of the host'
    }],
    'responses': {
        200: {'description': 'Agent successfully deleted'},
        401: {'description': 'Invalid or missing JWT token'},
        404: {'description': 'Agent not found or does not exist'},
        429: {'description': 'Too many requests: rate limit exceeded'},
        500: {'description': 'Internal server error'}
    }
})
def delete_agent(agent_id):
    agent=db.get_or_404(Agent, agent_id)

    try:
        db.session.execute(delete(MetricLog).where(MetricLog.agent_id==agent.id))
        db.session.delete(agent)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete agent str{e}'}), 500

    return jsonify({
        'message':'Agent successfully deleted',
    }), 200
@app.route('/')
def index():
    token = create_access_token(identity="dashboard")
    return render_template('index.html', token=token)

@app.route('/favicon.ico')
@limiter.exempt
def favicon():
    return '', 204


if __name__ == '__main__':
    app.run()
