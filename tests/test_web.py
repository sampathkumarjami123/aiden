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


if __name__ == '__main__':
    unittest.main()
