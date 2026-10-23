import json
import os
import unittest

from sqlalchemy import select


from api.app import app
from db.database import db
from model.models import Agent


class TelemetryAPITestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED']=False

        os.environ['AGENT_PASSWORD'] = 'test_password'

        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def get_auth_token(self):
        """Helper function to log in and get a JWT token"""
        response = self.client.post('/api/login', json={
            'hostname': 'test_agent',
            'password': 'test_password'
        })
        data = json.loads(response.data)
        return data.get('access_token')

    def test_1_login_success(self):
        """Test that login returns 200 and access_token"""
        response = self.client.post('/api/login', json={
            'hostname': 'test_agent',
            'password': 'test_password'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('access_token', json.loads(response.data))

    def test_2_metrics(self):
        """Test that an authenticated user can POST metrics"""
        token = self.get_auth_token()
        headers = {'Authorization': f'Bearer {token}'}


        payload = {
            'hostname': 'test_agent',
            'os_info': 'Linux',
            'cpu_percent': 45.0,
            'ram_percent': 65.0,
            'disk_percent': 80.0,
            'total_ram_gb': 16,
            'total_disk_gb': 22,
        }

        response = self.client.post('/api/metrics', json=payload, headers=headers)
        self.assertEqual(response.status_code, 201)
        self.assertIn('success', str(response.data).lower())

    def test_3_get_hosts(self):
        """Test that /api/hosts returns the active host list"""
        token = self.get_auth_token()
        headers = {'Authorization': f'Bearer {token}'}
        self.client.post('/api/metrics', json={
            'hostname':'test_agent',
            'os_info': 'Linux',
            'cpu_percent': 10.0,
            'ram_percent': 20.0,
            'disk_percent': 30.0,
            'total_ram_gb': 8.0,
            'total_disk_gb': 250.0
        }, headers=headers)
        response = self.client.get('/api/hosts', headers=headers)
        self.assertEqual(response.status_code, 200)

        data=json.loads(response.data)
        self.assertTrue(len(data) > 0)
        self.assertEqual(data[0]['host']['hostname'], 'test_agent')

    def test_4_unauthorization_access(self):
        response = self.client.post('/api/metrics', json={
            'hostname': 'unauthorization_agent',
            'cpu_percent': 15.0,
        })
        self.assertIn(response.status_code, [401, 422])

    def test_5_get_agent_history(self):
        """Test that an authenticated user can fetch history for a specific agent ID"""
        token = self.get_auth_token()
        headers = {'Authorization': f'Bearer {token}'}

        # 1. Post a metric to guarantee an agent exists in the database
        self.client.post('/api/metrics', json={
            'hostname': 'history_agent',
            'os_info': 'Linux',
            'cpu_percent': 55.0,
            'ram_percent': 70.0,
            'disk_percent': 40.0,
            'total_ram_gb': 16.0,
            'total_disk_gb': 500.0
        }, headers=headers)

        # 2. Request the history for agent ID 1 (since it's a fresh in-memory DB, ID 1 will be our agent)
        response = self.client.get('/api/hosts/1/history', headers=headers)

        # 3. Assert it succeeded and contains the expected structure
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn('host', data)
        self.assertIn('history', data)
        self.assertEqual(data['host']['hostname'], 'history_agent')
        self.assertTrue(len(data['history']) > 0)

    def test_6_get_agent_history_not_found(self):
        """Test that requesting history for a non-existent agent ID returns a 404"""
        token = self.get_auth_token()
        headers = {'Authorization': f'Bearer {token}'}

        response = self.client.get('/api/hosts/9999/history', headers=headers)
        self.assertEqual(response.status_code, 404)

    def test_7_update_agent(self):
        """Test that an authenticated user can update an agent (CRUD - Update)"""
        token = self.get_auth_token()
        headers = {'Authorization': f'Bearer {token}'}

        self.client.post('/api/metrics', json={
            'hostname': 'update_agent',
            'os_info': 'Linux',
            'cpu_percent': 15.0,
            'ram_percent': 20.0,
            'disk_percent': 30.0,
            'total_ram_gb': 16.0,
            'total_disk_gb': 22,
        }, headers=headers)

        agent = db.session.execute(select(Agent).filter(Agent.hostname == 'update_agent')).scalar_one_or_none()
        self.assertIsNotNone(agent)

        response = self.client.put(f'/api/hosts/{agent.id}', json={
            'hostname': 'new_update_agent',
            'os_info': 'Ubuntu',
        }, headers=headers)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn(data['host']['hostname'], 'new_update_agent')

    def test_8_delete_agent(self):
        """Test that an authenticated user can delete an agent and its logs (CRUD - Delete)"""
        token = self.get_auth_token()
        headers = {'Authorization': f'Bearer {token}'}

        self.client.post('/api/metrics', json={
            'hostname': 'doomed_agent',
            'os_info': 'Linux',
            'cpu_percent': 15.0,
            'ram_percent': 20.0,
            'disk_percent': 30.0,
            'total_ram_gb': 16.0,
            'total_disk_gb': 22,
        }, headers=headers)

        agent=db.session.query(Agent).filter(Agent.hostname == 'doomed_agent').first()
        self.assertIsNotNone(agent)

        response = self.client.delete(f'/api/hosts/{agent.id}', headers=headers)
        self.assertEqual(response.status_code, 200)

        check_response=self.client.get(f'/api/hosts/{agent.id}/history', headers=headers)
        self.assertEqual(check_response.status_code, 404)


    if __name__ == '__main__':
        unittest.main(verbosity=2)
