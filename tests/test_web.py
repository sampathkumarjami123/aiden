import unittest

from fastapi.testclient import TestClient

from aiden_web import app


class WebApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload.get('ok'), True)
        self.assertEqual(payload.get('service'), 'aiden-web')

    def test_state_endpoint_shape(self):
        response = self.client.get('/api/state')
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        for key in ('prefs', 'profiles', 'tasks', 'memory_notes', 'runtime'):
            self.assertIn(key, payload)

    def test_invalid_profile_switch_returns_400(self):
        response = self.client.post('/api/profiles/switch', json={'name': 'does-not-exist'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_invalid_task_done_returns_400(self):
        response = self.client.post('/api/tasks/done', json={'task_id': 99999})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_invalid_chat_mode_returns_400(self):
        response = self.client.post('/api/chat', json={'message': 'hello', 'mode': 'invalid'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())


if __name__ == '__main__':
    unittest.main()
