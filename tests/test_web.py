import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

import aiden_web
from aiden_web import app


class WebApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        aiden_web._clear_rate_limit_state()

    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload.get('ok'), True)
        self.assertEqual(payload.get('service'), 'aiden-web')

    def test_state_endpoint_shape(self):
        response = self.client.get('/api/state')
        self.assertEqual(response.status_code, 200)
        self.assertIn('x-request-id', response.headers)
        payload = response.json()
        for key in ('prefs', 'profiles', 'tasks', 'memory_notes', 'runtime'):
            self.assertIn(key, payload)

    def test_invalid_profile_switch_returns_400(self):
        response = self.client.post('/api/profiles/switch', json={'name': 'does-not-exist'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('x-request-id', response.headers)
        self.assertIn('error', response.json())

    def test_invalid_task_done_returns_400(self):
        response = self.client.post('/api/tasks/done', json={'task_id': 99999})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_invalid_chat_mode_returns_400(self):
        response = self.client.post('/api/chat', json={'message': 'hello', 'mode': 'invalid'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_request_too_large_returns_413(self):
        with patch('aiden_web.MAX_REQUEST_BYTES', 8):
            response = self.client.post('/api/chat', json={'message': 'this payload is too large'})
        self.assertEqual(response.status_code, 413)
        self.assertIn('x-request-id', response.headers)
        self.assertIn('error', response.json())

    def test_rate_limit_returns_429(self):
        with patch('aiden_web.RATE_LIMIT_REQUESTS_PER_WINDOW', 2):
            first = self.client.get('/api/state')
            second = self.client.get('/api/state')
            third = self.client.get('/api/state')

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(third.status_code, 429)
        self.assertIn('x-request-id', third.headers)
        self.assertIn('error', third.json())


if __name__ == '__main__':
    unittest.main()
